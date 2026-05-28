from __future__ import annotations

from datetime import date

from src.models.bug_report import BugReport
from src.models.enhancement_request import EnhancementRequest
from src.models.member_verify import MemberVerify

# 폼 모델 + 회원 → 시트 행(dict). 자동 컬럼만 채우고 운영자 컬럼은 키를 넣지 않아
# GoogleSheetAdapter가 빈칸으로 두게 한다(사람이 채운 값 보존). 상세 내용은 이슈 본문에.


def bug_to_row(
    report: BugReport,
    member: MemberVerify,
    issue_number: int | None = None,
    today: str | None = None,
) -> dict[str, str]:
    return {
        "등록일": today or date.today().isoformat(),
        "등록자": member.name,
        "팀": member.team,
        "테스트 계정": report.test_account or "",
        "테스트 영역": report.area,
        "세부 기능": report.detailed_feature or "",
        "발생 증상": report.actual_behavior or "",
        "발생 빈도": report.frequency or "",
        "우선순위": report.severity.value,
        "처리 상태": "접수",
        "# github issue": f"#{issue_number}" if issue_number is not None else "",
        "비고": report.additional_comments or "",
    }


def enhancement_to_row(
    report: EnhancementRequest,
    member: MemberVerify,
    issue_number: int | None = None,
    today: str | None = None,
) -> dict[str, str]:
    return {
        "등록일": today or date.today().isoformat(),
        "등록자": member.name,
        "팀": member.team,
        "테스트 영역": report.area,
        "세부 기능": report.feature_to_improve,
        "발생 화면": report.screen_url,
        "우선순위": report.priority.value,
        "처리 상태": "검토",
        "비고": report.additional_comments or "",
        "# github issue": f"#{issue_number}" if issue_number is not None else "",
    }
