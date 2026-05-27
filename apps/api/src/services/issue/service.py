from __future__ import annotations

from src.models.bug_report import BugReport
from src.models.enhancement_request import EnhancementRequest
from src.models.issue_draft import IssueDraft
from src.models.member_verify import MemberVerify
from src.services.github.port import GitHubPort

_TITLE_MAX = 60


class IssueService:
    """폼 입력(BugReport/EnhancementRequest) + 회원 메타데이터 → GitHub Issue 초안.

    본문 마크다운 변환과 라벨 부여는 이 서비스의 책임이며(아키텍처 설계서 §3.1),
    GitHubPort(ABC)에만 의존한다. 라벨은 저장소에 실재하는 라벨만 사용한다:
    - 타입: ``bug`` / ``enhancement`` (ADR-006: bug만 LLM·분석 PR 대상)
    - 우선순위: ``priority:P1``~``priority:P4`` (bug 한정, docs/operations/severity_policy.md)
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
        body = "\n".join(
            [
                "## 설명",
                report.description,
                "",
                "## 재현 절차",
                report.reproduction_steps,
                "",
                "## 테스트 환경",
                report.test_environment,
                *(["", "## 첨부", report.image_url] if report.image_url else []),
                "",
                "---",
                *self._reporter_footer(member, report.area),
                f"- Severity: {report.severity.value}",
            ]
        )
        return IssueDraft(
            title=self._title("Bug", report.area, report.description),
            body=body,
            labels=["bug", f"priority:{report.severity.value}"],
        )

    def _build_enhancement(self, report: EnhancementRequest, member: MemberVerify) -> IssueDraft:
        body = "\n".join(
            [
                "## 설명",
                report.description,
                "",
                "## 기대 동작",
                report.expected_behavior,
                "",
                "---",
                *self._reporter_footer(member, report.area),
            ]
        )
        return IssueDraft(
            title=self._title("Enhancement", report.area, report.description),
            body=body,
            labels=["enhancement"],
        )

    @staticmethod
    def _reporter_footer(member: MemberVerify, area: str) -> list[str]:
        return [
            f"- 제출자: {member.name} ({member.team})",
            f"- 이메일: {member.email}",
            f"- 영역: {area}",
        ]

    @staticmethod
    def _title(kind: str, area: str, description: str) -> str:
        summary = description.splitlines()[0].strip() if description.strip() else ""
        if len(summary) > _TITLE_MAX:
            summary = summary[: _TITLE_MAX - 1].rstrip() + "…"
        return f"[{kind}][{area}] {summary}"
