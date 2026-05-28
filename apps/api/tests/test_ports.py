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
        title="제목 테스트",
        reporter_email="a@b.co",
        screen_url="https://app.example.com/x",
        area="Search",
        severity=Severity.P3,
        actual_behavior="d",
        reproduction_steps=["s"],
    )


def _enh() -> EnhancementRequest:
    return EnhancementRequest(
        title="제목 테스트",
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
    # analyze 는 여전히 미구현(W3 대기). is_healthy 와 summarize_pr_close 는
    # LLM 키가 없을 때의 정상 fallback 으로 동작 → False / None 반환.
    from src.services.llm.port import PRCloseContext

    adapter = DummyLLMAdapter()
    with pytest.raises(NotImplementedError):
        adapter.analyze(_bug())
    assert adapter.is_healthy() is False
    assert (
        adapter.summarize_pr_close(
            PRCloseContext(
                issue_number=1,
                issue_title="t",
                issue_body="b",
                pr_number=2,
                pr_title="pt",
                pr_body="pb",
                pr_url="https://x/2",
                merged=True,
                merge_commit_sha="abc",
            )
        )
        is None
    )


def test_dummy_sheet_raises_not_implemented() -> None:
    adapter = DummySheetAdapter()
    with pytest.raises(NotImplementedError):
        adapter.append_bug({"issue_number": 1})
    with pytest.raises(NotImplementedError):
        adapter.append_enhancement({"issue_number": 1})
    with pytest.raises(NotImplementedError):
        adapter.list_issues()
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
