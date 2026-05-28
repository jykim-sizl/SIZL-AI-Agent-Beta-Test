from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Body
from pydantic import BaseModel

from src.api.deps import GitHubDep, IssueServiceDep, MemberServiceDep, SheetDep
from src.core.config import settings
from src.core.logging import logger
from src.models.bug_report import BugReport
from src.models.enhancement_request import EnhancementRequest
from src.services.sheet.mapping import bug_to_row, enhancement_to_row

router = APIRouter()

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
def list_issues(sheet: SheetDep) -> list[dict[str, Any]]:
    # 구글 시트(Raw Bugs/Enhancements) → 목록. 프론트 내 이슈/대시보드가 사용.
    issues = sheet.list_issues()
    for item in issues:
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
    # title/body 수정. comment 가 주어지면 별도 코멘트로 게시.
    title: str | None = None
    body: str | None = None
    comment: str | None = None


@router.patch("/issues/{number}")
def update_issue(number: int, patch: IssuePatch, github: GitHubDep) -> dict[str, str]:
    if patch.title is not None or patch.body is not None:
        # title/body 중 하나만 보내도 GitHub 가 부분 업데이트를 지원하지만,
        # 우리 케이스는 모달이 둘 다 보냄 → 둘 다 안전하게 전달.
        current = github.get_issue(number)
        title = patch.title if patch.title is not None else current["title"]
        body = patch.body if patch.body is not None else current["body"]
        github.update_issue(number, title=title, body=body)
    if patch.comment and patch.comment.strip():
        github.add_comment(number, patch.comment.strip())
    logger.info("issue_edited", number=number, has_comment=bool(patch.comment))
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
    # 3) 시트 기입 (운영자 컬럼은 빈칸 유지). 버그/개선 탭 분리.
    if isinstance(report, BugReport):
        kind: Literal["bug", "enhancement"] = "bug"
        sheet.append_bug(bug_to_row(report, member, number))
    else:
        kind = "enhancement"
        sheet.append_enhancement(enhancement_to_row(report, member, number))

    logger.info("issue_submitted", kind=kind, number=number, email=member.email, area=report.area)
    return IssueAccepted(
        kind=kind, issue_number=number, email=member.email, name=member.name, team=member.team
    )
