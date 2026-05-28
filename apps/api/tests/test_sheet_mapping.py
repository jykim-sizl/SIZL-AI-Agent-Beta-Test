from __future__ import annotations

from src.models.bug_report import BugReport
from src.models.enhancement_request import EnhancementRequest
from src.models.member_verify import MemberVerify
from src.services.sheet.mapping import bug_to_row, enhancement_to_row

MEMBER = MemberVerify(email="jy_kim@sizl.co.kr", name="김정연", team="Neo Lab")


def test_bug_to_row_fills_auto_columns_only() -> None:
    report = BugReport(
        reporter_email="jy_kim@sizl.co.kr",
        test_account="qa@company.com",
        screen_url="https://app.example.com/x",
        area="Search",
        severity="P1",
        actual_behavior="빈 결과",
    )
    row = bug_to_row(report, MEMBER, issue_number=142, today="2026-05-27")
    assert row["등록일"] == "2026-05-27"
    assert row["등록자"] == "김정연"
    assert row["팀"] == "Neo Lab"
    assert row["우선순위"] == "P1"
    assert row["처리 상태"] == "접수"
    assert row["# github issue"] == "#142"
    assert row["테스트 계정"] == "qa@company.com"
    # 시트 미포함 항목(보고용 간소화)은 매핑에서 빠진다 — 이슈 본문엔 유지
    for excluded in ("발생 화면", "테스트 시나리오"):
        assert excluded not in row
    # 운영자 수기 컬럼도 키 없음 (어댑터가 빈칸으로 두어 보존)
    for operator_col in ("테스트 담당자", "조치 내용", "배포 여부"):
        assert operator_col not in row


def test_enhancement_to_row() -> None:
    report = EnhancementRequest(
        reporter_email="jy_kim@sizl.co.kr",
        screen_url="https://app.example.com/y",
        area="Chat",
        priority="P3",
        feature_to_improve="전송 단축키",
    )
    row = enhancement_to_row(report, MEMBER, today="2026-05-27")
    assert row["처리 상태"] == "검토"
    assert row["세부 기능"] == "전송 단축키"
    assert row["우선순위"] == "P3"
    assert "재현 여부" not in row
    assert "원인 유형" not in row
