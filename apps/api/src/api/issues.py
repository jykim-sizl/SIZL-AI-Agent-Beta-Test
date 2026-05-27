from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Body
from pydantic import BaseModel

from src.api.deps import MemberServiceDep
from src.core.logging import logger
from src.models.bug_report import BugReport
from src.models.enhancement_request import EnhancementRequest

router = APIRouter()

# bug/enhancement는 필수 필드가 서로 다르고 두 모델 모두 extra=forbid이므로
# 스마트 유니온이 페이로드를 명확히 구분한다 (별도 판별 필드 불필요).
IssueSubmission = Annotated[BugReport | EnhancementRequest, Body()]


class IssueAccepted(BaseModel):
    status: Literal["accepted"] = "accepted"
    kind: Literal["bug", "enhancement"]
    email: str
    name: str
    team: str


@router.post("/issues", response_model=IssueAccepted)
def submit_issue(report: IssueSubmission, members: MemberServiceDep) -> IssueAccepted:
    # 회원 검증을 가장 먼저 수행한다. 미등재면 MemberService가 403을 발생시킨다.
    # GitHub Issue 생성 / Sheet 기록은 W2 — 여기서는 검증까지만 확정한다.
    member = members.verify(str(report.tester_email))
    kind: Literal["bug", "enhancement"] = "bug" if isinstance(report, BugReport) else "enhancement"
    logger.info("issue_submission_accepted", kind=kind, email=member.email, area=report.area)
    return IssueAccepted(kind=kind, email=member.email, name=member.name, team=member.team)
