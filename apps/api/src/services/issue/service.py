from __future__ import annotations

import base64

from src.models.attachment import AttachmentInput
from src.models.bug_report import BugReport
from src.models.enhancement_request import EnhancementRequest
from src.models.issue_draft import IssueDraft
from src.models.member_verify import MemberVerify
from src.services.github.port import GitHubPort

_TITLE_MAX = 60


class IssueService:
    """폼 입력(BugReport/EnhancementRequest) + 회원 메타데이터 → GitHub Issue 초안.

    본문 마크다운 변환과 라벨 부여가 책임이며 GitHubPort(ABC)에만 의존한다.
    상세 필드는 본문에 담고, 라벨은 저장소 실재 라벨만 사용한다:
    - 타입: ``bug`` / ``enhancement`` (ADR-006: bug만 LLM·분석 PR 대상)
    - 우선순위: ``priority:P1``~``priority:P4`` (bug 한정)
    """

    def __init__(self, github: GitHubPort) -> None:
        self._github = github

    def submit(self, report: BugReport | EnhancementRequest, member: MemberVerify) -> int:
        draft = self.build_draft(report, member)
        return self._github.create_issue(draft)

    def build_draft(
        self, report: BugReport | EnhancementRequest, member: MemberVerify
    ) -> IssueDraft:
        if isinstance(report, BugReport):
            return self._build_bug(report, member)
        return self._build_enhancement(report, member)

    def _build_bug(self, report: BugReport, member: MemberVerify) -> IssueDraft:
        env = " / ".join(filter(None, [report.os, report.browser, report.device, report.network]))
        steps = "\n".join(f"{i}. {s}" for i, s in enumerate(report.reproduction_steps, 1))
        # 섹션 mode: "bullet"(기본·평문은 자동 bullet화) / "code"(``` 감쌈) / "raw"(그대로)
        sections: list[tuple[str, str | None, str]] = [
            ("## 발생 증상", report.actual_behavior, "bullet"),
            ("## 예상 동작", report.expected_behavior, "bullet"),
            ("## 상세 기능", report.detailed_feature, "bullet"),
            ("## 테스트 시나리오", report.scenario_description, "bullet"),
            ("## 재현 절차", steps or None, "bullet"),
            ("## 입력 값", report.input_value, "bullet"),
            ("## 실제 출력", report.actual_output, "bullet"),
            ("## 예상 출력", report.expected_output, "bullet"),
            ("## 테스트 환경", env or None, "bullet"),
            ("## 콘솔/에러 로그", report.error_log, "code"),
            ("## 첨부", self._attachments_md(report.attachments), "raw"),
            ("## 추가 의견", report.additional_comments, "bullet"),
        ]
        access = (report.access_time or "").replace("T", " ")  # 'YYYY-MM-DDTHH:MM' → 공백
        footer = [
            *self._reporter_footer(member, report.area),
            f"- 발생 화면: {report.screen_url}",
            *([f"- 테스트 계정: {report.test_account}"] if report.test_account else []),
            *([f"- 접근 시간: {access}"] if access else []),
            *([f"- 발생 빈도: {report.frequency}"] if report.frequency else []),
            f"- Severity: {report.severity.value}",
        ]
        body = self._compose(sections, footer)
        return IssueDraft(
            title=self._title("bug", report.area, report.title),
            body=body,
            labels=["bug", f"priority:{report.severity.value}"],
        )

    def _build_enhancement(self, report: EnhancementRequest, member: MemberVerify) -> IssueDraft:
        sections: list[tuple[str, str | None, str]] = [
            ("## 개선할 기능", report.feature_to_improve, "bullet"),
            ("## 현재 동작", report.current_behavior, "bullet"),
            ("## 기대 동작", report.expected_behavior, "bullet"),
            ("## 기대 효과", report.rationale, "bullet"),
            ("## 첨부", self._attachments_md(report.attachments), "raw"),
            ("## 추가 의견", report.additional_comments, "bullet"),
        ]
        footer = [
            *self._reporter_footer(member, report.area),
            f"- 관련 화면: {report.screen_url}",
            f"- 우선순위: {report.priority.value}",
        ]
        body = self._compose(sections, footer)
        return IssueDraft(
            title=self._title("enhance", report.area, report.title),
            body=body,
            labels=["enhancement"],
        )

    def _attachments_md(self, attachments: list[AttachmentInput]) -> str | None:
        # 이미지(data_url)는 업로드 후 ![](url)로 본문에 삽입, 그 외는 파일명만 표기.
        if not attachments:
            return None
        lines: list[str] = []
        for att in attachments:
            data_url = att.data_url or ""
            if data_url.startswith("data:image") and "," in data_url:
                content = base64.b64decode(data_url.split(",", 1)[1])
                url = self._github.upload_image(att.name, content)
                lines.append(f"![{att.name}]({url})")
            else:
                lines.append(f"- {att.name}")
        return "\n".join(lines)

    @staticmethod
    def _compose(sections: list[tuple[str, str | None, str]], footer: list[str]) -> str:
        # '## 요약' 으로 시작해 메타(제출자·이메일·영역 등)를 상단에 두고, 본문 섹션은
        # mode 에 따라 자동 bullet 화 / code-block 감쌈 / raw 그대로.
        parts: list[str] = ["## 요약", *footer, "---"]
        for heading, content, mode in sections:
            if not content:
                continue
            if mode == "code":
                body = f"```\n{content}\n```"
            elif mode == "raw":
                body = content
            else:  # bullet (default)
                body = IssueService._bulletize(content)
            parts.append(f"{heading}\n{body}\n")
        return "\n".join(parts)

    @staticmethod
    def _bulletize(text: str) -> str:
        # 평문 줄에 '- ' prefix 를 붙여 GitHub 에서 bullet 으로 렌더되게 한다.
        # 이미 마크다운(리스트/제목/인용/이미지/코드블록/숫자목록)이면 보존.
        markers = ("- ", "* ", "+ ", "# ", "> ", "![", "|", "<")
        result: list[str] = []
        in_code = False
        for raw in text.splitlines():
            line = raw.rstrip()
            if not line.strip():
                # 빈 줄: bullet 그룹 사이 구분으로 둠 (단, 연속된 빈 줄은 1줄로)
                if result and result[-1] != "":
                    result.append("")
                continue
            stripped = line.lstrip()
            if stripped.startswith("```"):
                in_code = not in_code
                result.append(line)
                continue
            if in_code:
                result.append(line)
                continue
            if any(stripped.startswith(m) for m in markers):
                result.append(line)
                continue
            # 1. ~ 99. 숫자 리스트
            head = stripped.split(" ", 1)[0]
            if head.endswith(".") and head[:-1].isdigit():
                result.append(line)
                continue
            result.append(f"- {line}")
        return "\n".join(result)

    @staticmethod
    def _reporter_footer(member: MemberVerify, area: str) -> list[str]:
        return [
            f"- 제출자: {member.name} ({member.team})",
            f"- 이메일: {member.email}",
            f"- 영역: {area}",
        ]

    @staticmethod
    def _title(type_: str, area: str, summary: str) -> str:
        # 기존 repo 컨벤션: bug(영역): 요약 / enhance(영역): 요약
        text = summary.splitlines()[0].strip() if summary.strip() else "(제목 없음)"
        if len(text) > _TITLE_MAX:
            text = text[: _TITLE_MAX - 1].rstrip() + "…"
        return f"{type_}({area}): {text}"
