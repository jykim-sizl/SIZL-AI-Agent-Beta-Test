from __future__ import annotations

import pytest

from src.adapters.impl import (
    DummyGitHubAdapter,
    DummyIssueAdapter,
    DummyLLMAdapter,
    DummySheetAdapter,
)
from src.adapters.ports import GitHubPort, IssuePort, LLMPort, SheetPort
from src.models.analysis_result import AnalysisResult
from src.models.bug_report import BugReport, Severity
from src.models.enhancement_request import EnhancementRequest


def _bug() -> BugReport:
    return BugReport(
        tester_email="a@b.co",
        area="Search",
        severity=Severity.P3,
        test_environment="env",
        description="d",
        reproduction_steps="s",
    )


def _enh() -> EnhancementRequest:
    return EnhancementRequest(
        tester_email="a@b.co",
        area="Dash",
        description="d",
        expected_behavior="e",
    )


def _analysis() -> AnalysisResult:
    return AnalysisResult(
        cause_hypothesis="c",
        reproduction_summary="r",
        developer_guide="g",
        original_issue_url="https://github.com/o/r/issues/1",
    )


@pytest.mark.parametrize(
    "port",
    [GitHubPort, IssuePort, LLMPort, SheetPort],
)
def test_port_is_abstract(port: type) -> None:
    with pytest.raises(TypeError):
        port()  # type: ignore[abstract]


def test_dummy_llm_raises_not_implemented() -> None:
    adapter = DummyLLMAdapter()
    with pytest.raises(NotImplementedError):
        adapter.analyze(_bug())
    with pytest.raises(NotImplementedError):
        adapter.is_healthy()


def test_dummy_sheet_raises_not_implemented() -> None:
    adapter = DummySheetAdapter()
    with pytest.raises(NotImplementedError):
        adapter.append_bug({"issue_number": 1})
    with pytest.raises(NotImplementedError):
        adapter.append_enhancement({"issue_number": 1})
    with pytest.raises(NotImplementedError):
        adapter.update_pr_status(1, "open")


def test_dummy_github_raises_not_implemented() -> None:
    adapter = DummyGitHubAdapter()
    with pytest.raises(NotImplementedError):
        adapter.create_issue(_bug())
    with pytest.raises(NotImplementedError):
        adapter.create_issue(_enh())
    with pytest.raises(NotImplementedError):
        adapter.create_empty_pr(1, _analysis())
    with pytest.raises(NotImplementedError):
        adapter.close_issue(1)


def test_dummy_issue_raises_not_implemented() -> None:
    adapter = DummyIssueAdapter()
    with pytest.raises(NotImplementedError):
        adapter.submit(_bug())
