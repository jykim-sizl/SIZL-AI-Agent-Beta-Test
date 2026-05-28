from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models.analysis_result import AnalysisResult
from src.models.bug_report import BugReport, Severity
from src.models.enhancement_request import EnhancementRequest, Priority
from src.models.member_verify import MemberVerify

VALID_BUG = {
    "title": "제목 테스트",
    "reporter_email": "alice@sizl.co.kr",
    "test_account": "qa@company.com",
    "screen_url": "https://app.example.com/search",
    "area": "Search",
    "severity": "P2",
    "actual_behavior": "검색 결과가 비어있다",
    "reproduction_steps": ["검색창에 'foo' 입력", "결과 0건"],
}


def test_bug_report_accepts_valid_payload() -> None:
    bug = BugReport(**VALID_BUG)
    assert bug.severity is Severity.P2
    assert bug.attachments == []
    assert bug.test_account == "qa@company.com"


def test_bug_report_accepts_camelcase_aliases() -> None:
    # 프론트가 보내는 camelCase 키를 그대로 수용한다.
    bug = BugReport(
        title="제목 테스트",
        reporterEmail="alice@sizl.co.kr",
        screenUrl="https://app.example.com/x",
        area="Search",
        severity="P1",
    )
    assert bug.screen_url == "https://app.example.com/x"
    assert bug.severity is Severity.P1


def test_bug_report_rejects_invalid_email() -> None:
    payload = {**VALID_BUG, "reporter_email": "not-an-email"}
    with pytest.raises(ValidationError):
        BugReport(**payload)


def test_bug_report_rejects_unknown_severity() -> None:
    payload = {**VALID_BUG, "severity": "P9"}
    with pytest.raises(ValidationError):
        BugReport(**payload)


def test_bug_report_rejects_missing_required_field() -> None:
    payload = {**VALID_BUG}
    del payload["screen_url"]  # 발생 화면 URL 필수
    with pytest.raises(ValidationError):
        BugReport(**payload)


def test_bug_report_rejects_extra_field() -> None:
    payload = {**VALID_BUG, "unexpected": "x"}
    with pytest.raises(ValidationError):
        BugReport(**payload)


def test_enhancement_request_minimal_valid() -> None:
    req = EnhancementRequest(
        title="제목 테스트",
        reporter_email="bob@sizl.co.kr",
        screen_url="https://app.example.com/dashboard",
        area="Dashboard",
        priority="P3",
        feature_to_improve="팀별 필터 추가",
    )
    assert req.area == "Dashboard"
    assert req.priority is Priority.P3


def test_member_verify_holds_email_name_team() -> None:
    m = MemberVerify(
        email="alice@sizl.co.kr",
        name="Alice",
        team="QA",
    )
    assert (m.email, m.name, m.team) == ("alice@sizl.co.kr", "Alice", "QA")


def test_member_verify_rejects_unknown_field() -> None:
    """position·is_active 등 시스템에서 쓰지 않는 필드는 거부 (extra=forbid)."""
    with pytest.raises(ValidationError):
        MemberVerify(
            email="a@b.co",
            name="A",
            team="T",
            is_active=True,
        )


def test_analysis_result_requires_url() -> None:
    with pytest.raises(ValidationError):
        AnalysisResult(
            cause_hypothesis="x",
            reproduction_summary="y",
            related_files=[],
            developer_guide="z",
            original_issue_url="not-a-url",
        )


def test_analysis_result_default_related_files_empty() -> None:
    result = AnalysisResult(
        cause_hypothesis="원인",
        reproduction_summary="재현",
        developer_guide="가이드",
        original_issue_url="https://github.com/org/repo/issues/1",
    )
    assert result.related_files == []
