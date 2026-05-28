from __future__ import annotations

import pytest

from src.adapters.impl import (
    DummyGitHubAdapter,
    DummyIssueAdapter,
    DummyLLMAdapter,
    DummySheetAdapter,
)
from src.models.bug_report import BugReport, Severity
from src.models.enhancement_request import EnhancementRequest
from src.models.issue_draft import IssueDraft
from src.services.github import GitHubPort
from src.services.issue import IssuePort
from src.services.llm import LLMPort
from src.services.sheet import SheetPort


def _bug() -> BugReport:
    return BugReport(
        reporter_email="a@b.co",
        screen_url="https://app.example.com/x",
        area="Search",
        severity=Severity.P3,
        actual_behavior="d",
        reproduction_steps=["s"],
    )


def _enh() -> EnhancementRequest:
    return EnhancementRequest(
        reporter_email="a@b.co",
        screen_url="https://app.example.com/x",
        area="Dash",
        priority="P3",
        feature_to_improve="d",
        expected_behavior="e",
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
    draft = IssueDraft(title="t", body="b", labels=["bug"])
    with pytest.raises(NotImplementedError):
        adapter.create_issue(draft)
    with pytest.raises(NotImplementedError):
        adapter.create_empty_pr(1, "title", "body")
    with pytest.raises(NotImplementedError):
        adapter.upload_image("a.png", b"x")
    with pytest.raises(NotImplementedError):
        adapter.close_issue(1)


def test_dummy_issue_raises_not_implemented() -> None:
    adapter = DummyIssueAdapter()
    with pytest.raises(NotImplementedError):
        adapter.submit(_bug())
