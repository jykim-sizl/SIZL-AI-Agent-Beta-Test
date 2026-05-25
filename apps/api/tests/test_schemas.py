from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models.analysis_result import AnalysisResult
from src.models.bug_report import BugReport, Severity
from src.models.enhancement_request import EnhancementRequest
from src.models.member_verify import MemberVerify

VALID_BUG = {
    "tester_email": "alice@sizl.co.kr",
    "tester_name": "Alice",
    "area": "Search",
    "severity": "P2",
    "test_environment": "macOS 14, Chrome 125, Wi-Fi",
    "description": "검색 결과가 비어있다",
    "reproduction_steps": "1. 검색창에 'foo' 입력\n2. 결과 0건",
}


def test_bug_report_accepts_valid_payload() -> None:
    bug = BugReport(**VALID_BUG)
    assert bug.severity is Severity.P2
    assert bug.image_url is None


def test_bug_report_rejects_invalid_email() -> None:
    payload = {**VALID_BUG, "tester_email": "not-an-email"}
    with pytest.raises(ValidationError):
        BugReport(**payload)


def test_bug_report_rejects_unknown_severity() -> None:
    payload = {**VALID_BUG, "severity": "P9"}
    with pytest.raises(ValidationError):
        BugReport(**payload)


def test_bug_report_rejects_missing_required_field() -> None:
    payload = {**VALID_BUG}
    del payload["reproduction_steps"]
    with pytest.raises(ValidationError):
        BugReport(**payload)


def test_bug_report_rejects_extra_field() -> None:
    payload = {**VALID_BUG, "unexpected": "x"}
    with pytest.raises(ValidationError):
        BugReport(**payload)


def test_enhancement_request_minimal_valid() -> None:
    req = EnhancementRequest(
        tester_email="bob@sizl.co.kr",
        area="Dashboard",
        description="필터 추가 요청",
        expected_behavior="팀 별 필터가 우측 상단에 노출",
    )
    assert req.area == "Dashboard"


def test_member_verify_is_eligible_when_active() -> None:
    m = MemberVerify(
        email="alice@sizl.co.kr",
        name="Alice",
        team="QA",
        position="Engineer",
        is_active=True,
    )
    assert m.is_eligible() is True


def test_member_verify_not_eligible_when_inactive() -> None:
    m = MemberVerify(
        email="ex@sizl.co.kr",
        name="Ex",
        team="QA",
        is_active=False,
    )
    assert m.is_eligible() is False


def test_member_verify_position_optional() -> None:
    m = MemberVerify(email="a@b.co", name="A", team="T", is_active=True)
    assert m.position is None


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
