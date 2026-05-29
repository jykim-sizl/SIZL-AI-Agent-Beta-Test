from __future__ import annotations

import base64
import re
from datetime import date
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Body
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from src.api.deps import GitHubDep, IssueServiceDep, MemberServiceDep, SheetDep
from src.core.config import settings
from src.core.logging import logger
from src.models.attachment import AttachmentInput
from src.models.bug_report import BugReport
from src.models.enhancement_request import EnhancementRequest
from src.services.sheet.mapping import bug_to_row, enhancement_to_row

router = APIRouter()

# 'bug(영역): 제목' / 'enhance(영역): 제목' → '제목' 만 추출.
_TITLE_PREFIX = re.compile(r"^(?:bug|enhance)\([^)]+\):\s*")

# bug/enhancement는 필수 필드가 서로 다르고 두 모델 모두 extra=forbid이므로
# 스마트 유니온이 페이로드를 명확히 구분한다 (별도 판별 필드 불필요).
IssueSubmission = Annotated[BugReport | EnhancementRequest, Body()]


class IssueAccepted(BaseModel):
    status: Literal["accepted"] = "accepted"
    kind: Literal["bug", "enhancement"]
    issue_number: int
    email: str
    name: str
    team: str


@router.get("/issues")
def list_issues(sheet: SheetDep, github: GitHubDep) -> list[dict[str, Any]]:
    # 구글 시트(Raw Bugs/Enhancements) → 목록. 프론트 내 이슈/대시보드가 사용.
    # 제목은 GitHub 이슈 제목(사용자가 폼에 입력한 'title')으로 덮어씀 — 시트엔
    # 제목 컬럼이 없으므로(사용자 결정) GitHub 한 번 조회해 prefix 떼고 사용.
    issues = sheet.list_issues()
    try:
        gh_titles = github.list_issue_titles()
    except Exception as exc:  # noqa: BLE001 - GitHub 일시 오류로 목록 빈칸 되지 않게
        logger.warning("github_titles_fetch_failed", error=str(exc))
        gh_titles = {}
    for item in issues:
        if (full := gh_titles.get(item["number"])) is not None:
            stripped = _TITLE_PREFIX.sub("", full).strip()
            if stripped:
                item["title"] = stripped
        item["githubUrl"] = (
            f"https://github.com/{settings.github_issue_repo}/issues/{item['number']}"
        )
        if item.get("prNumber"):
            item["prUrl"] = (
                f"https://github.com/{settings.github_target_repo}/pull/{item['prNumber']}"
            )
    return issues


@router.get("/issues/{number}")
def get_issue(number: int, github: GitHubDep) -> dict[str, str]:
    # 단일 이슈 상세 (수정 모달 prefill 용 — title + body 풀로 받음).
    return github.get_issue(number)


class IssuePatch(BaseModel):
    """편집 모달이 보내는 페이로드. 모두 본문(body) 갱신으로 수렴.

    additional_comment 와 attachments 는 GitHub 코멘트가 아니라 **본문에 섹션으로 append**
    된다 (사용자 결정 2026-05-28: 본 페이지 편집 = 본문 수정, 코멘트 분리 없음).
    """

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    title: str | None = None
    body: str | None = None
    additional_comment: str | None = None
    attachments: list[AttachmentInput] = Field(default_factory=list)


@router.post("/issues/{number}/close")
def close_issue_route(number: int, github: GitHubDep, sheet: SheetDep) -> dict[str, str]:
    # 사용자 '닫기' 버튼 — webhook 의존 제거하고 직접 모든 동기화 수행
    # (이미 닫힌 이슈 재-close 도 시트 동기화 보장. ADR 2026-05-29).
    # 1) GitHub 이슈 close (이미 closed 면 no-op)
    github.close_issue(number, state_reason="not_planned")
    # 2) 시트 처리상태 + 조치 내용 (bug 가정 — 'not_planned' = '재현 불가')
    # 사용자가 명시적으로 '닫기' 한 의도는 unmerged-PR 시나리오와 유사하므로 '철회'/'재현 불가'
    # 사이 모호. 사용자 결정: 'not_planned' → 시트 '재현 불가' 로 매핑 (state_reason 매핑과 일관).
    action = (
        f"⚠️ #{number} 재현 불가 — 사용자가 웹폼 '닫기' 로 처리 (reason: not_planned)."
    )
    sheet.update_pr_status(number, "재현 불가", action_text=action)
    # 3) 열린 분석 PR 자동 close
    try:
        closed_pr = github.close_pr_for_issue(number)
        if closed_pr:
            logger.info("auto_closed_pr_with_user_close", issue=number, pr=closed_pr)
    except Exception as exc:  # noqa: BLE001
        logger.warning("pr_auto_close_failed_user_close", issue=number, error=str(exc))
    # 4) 이슈에 코멘트 (중복 게시 가능 — 받아들임)
    try:
        github.add_comment(number, action)
    except Exception as exc:  # noqa: BLE001
        logger.warning("issue_comment_failed_user_close", issue=number, error=str(exc))
    logger.info("issue_closed_by_user", number=number)
    return {"status": "closed"}


@router.patch("/issues/{number}")
def update_issue(number: int, patch: IssuePatch, github: GitHubDep) -> dict[str, str]:
    # title/body 둘 다 안전하게 보내도록 현재값과 머지.
    current = github.get_issue(number)
    title = patch.title if patch.title is not None else current["title"]
    body = patch.body if patch.body is not None else current["body"]

    # 추가 의견 → 본문 끝에 섹션으로 append (코멘트로 게시 안 함).
    extra_comment = (patch.additional_comment or "").strip()
    if extra_comment:
        today = date.today().isoformat()
        body = f"{body.rstrip()}\n\n## 추가 의견 ({today})\n{extra_comment}\n"

    # 첨부 → 이미지면 업로드 후 ![](url), 그 외는 파일명만. 본문 끝 섹션.
    if patch.attachments:
        today = date.today().isoformat()
        lines: list[str] = []
        for att in patch.attachments:
            data_url = att.data_url or ""
            if data_url.startswith("data:image") and "," in data_url:
                try:
                    content = base64.b64decode(data_url.split(",", 1)[1])
                    url = github.upload_image(att.name, content)
                    lines.append(f"![{att.name}]({url})")
                except Exception as exc:  # noqa: BLE001 - 업로드 실패해도 저장은 진행
                    logger.warning("attachment_upload_failed", name=att.name, error=str(exc))
                    lines.append(f"- {att.name} _(업로드 실패)_")
            else:
                lines.append(f"- {att.name}")
        if lines:
            body = f"{body.rstrip()}\n\n## 첨부 추가 ({today})\n" + "\n".join(lines) + "\n"

    github.update_issue(number, title=title, body=body)
    logger.info(
        "issue_edited",
        number=number,
        has_extra_comment=bool(extra_comment),
        attachments=len(patch.attachments),
    )
    return {"status": "updated"}


@router.post("/issues", response_model=IssueAccepted)
def submit_issue(
    report: IssueSubmission,
    members: MemberServiceDep,
    issues: IssueServiceDep,
    sheet: SheetDep,
) -> IssueAccepted:
    # 1) 회원 검증 (미등재면 403). 검증 대상은 로그인 이메일(reporter_email).
    member = members.verify(str(report.reporter_email))
    # 2) GitHub 이슈 생성 → 번호 확보
    number = issues.submit(report, member)
    # 3) Issue ID 발급 (BUG-NNN / REQ-NNN) + 시트 기입. 운영자 컬럼은 빈칸 유지.
    if isinstance(report, BugReport):
        kind: Literal["bug", "enhancement"] = "bug"
        issue_id = sheet.next_issue_id("bug")
        sheet.append_bug(bug_to_row(report, member, number, issue_id=issue_id))
    else:
        kind = "enhancement"
        issue_id = sheet.next_issue_id("enhancement")
        sheet.append_enhancement(
            enhancement_to_row(report, member, number, issue_id=issue_id)
        )

    logger.info("issue_submitted", kind=kind, number=number, email=member.email, area=report.area)
    return IssueAccepted(
        kind=kind, issue_number=number, email=member.email, name=member.name, team=member.team
    )
