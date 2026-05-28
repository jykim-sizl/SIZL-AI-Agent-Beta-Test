from __future__ import annotations

import pytest

from src.models.attachment import AttachmentInput
from src.models.bug_report import BugReport, Severity
from src.models.enhancement_request import EnhancementRequest
from src.models.issue_draft import IssueDraft
from src.models.member_verify import MemberVerify
from src.services.github import GitHubPort
from src.services.issue import IssueService


class RecordingGitHub(GitHubPort):
    """create_issue 호출을 기록하고 고정 이슈 번호를 돌려주는 테스트용 GitHubPort."""

    def __init__(self) -> None:
        self.created: list[IssueDraft] = []

    def create_issue(self, draft: IssueDraft) -> int:
        self.created.append(draft)
        return 101

    def create_empty_pr(self, issue_number: int, title: str, body: str) -> int:  # pragma: no cover
        raise NotImplementedError

    def upload_image(self, filename: str, content: bytes) -> str:
        return f"https://example.com/{filename}"

    def close_issue(self, issue_number: int) -> None:  # pragma: no cover
        raise NotImplementedError


MEMBER = MemberVerify(email="jy_kim@sizl.co.kr", name="김정연", team="Neo Lab")


def _bug(severity: Severity = Severity.P2) -> BugReport:
    return BugReport(
        reporter_email="jy_kim@sizl.co.kr",
        test_account="qa@company.com",
        screen_url="https://app.example.com/search",
        area="Search",
        severity=severity,
        os="macOS",
        browser="Chrome",
        actual_behavior="검색 결과가 비어 있음",
        expected_behavior="결과가 표시되어야 함",
        reproduction_steps=["검색", "엔터"],
        attachments=[AttachmentInput(name="shot.png")],
    )


def _enh() -> EnhancementRequest:
    return EnhancementRequest(
        reporter_email="jy_kim@sizl.co.kr",
        screen_url="https://app.example.com/dashboard",
        area="Dashboard",
        priority="P3",
        feature_to_improve="팀별 필터 요청",
        expected_behavior="우측 상단 필터 노출",
    )


@pytest.mark.parametrize(
    ("severity", "expected_label"),
    [
        (Severity.P1, "priority:P1"),
        (Severity.P2, "priority:P2"),
        (Severity.P3, "priority:P3"),
        (Severity.P4, "priority:P4"),
    ],
)
def test_bug_labels_include_bug_and_priority(severity: Severity, expected_label: str) -> None:
    draft = IssueService(RecordingGitHub()).build_draft(_bug(severity), MEMBER)
    assert draft.labels == ["bug", expected_label]


def test_bug_body_contains_sections_and_reporter() -> None:
    draft = IssueService(RecordingGitHub()).build_draft(_bug(), MEMBER)
    assert draft.title == "[Bug][Search] 검색 결과가 비어 있음"
    for fragment in (
        "## 발생 증상",
        "## 재현 절차",
        "## 테스트 환경",
        "김정연 (Neo Lab)",
        "발생 화면: https://app.example.com/search",
        "Severity: P2",
        "shot.png",  # 첨부 파일명 포함
    ):
        assert fragment in draft.body


def test_image_attachment_embedded_in_body() -> None:
    report = _bug().model_copy(
        update={
            "attachments": [
                AttachmentInput(name="cap.png", data_url="data:image/png;base64,aGVsbG8=")
            ]
        }
    )
    draft = IssueService(RecordingGitHub()).build_draft(report, MEMBER)
    assert "![cap.png](https://example.com/cap.png)" in draft.body


def test_enhancement_label_is_enhancement_only() -> None:
    draft = IssueService(RecordingGitHub()).build_draft(_enh(), MEMBER)
    assert draft.labels == ["enhancement"]
    assert draft.title == "[Enhancement][Dashboard] 팀별 필터 요청"
    assert "## 개선할 기능" in draft.body
    assert "우선순위: P3" in draft.body


def test_title_truncates_long_summary() -> None:
    long = "가" * 100
    report = _bug().model_copy(update={"actual_behavior": long})
    draft = IssueService(RecordingGitHub()).build_draft(report, MEMBER)
    assert draft.title.endswith("…")
    assert len(draft.title) < len(f"[Bug][Search] {long}")


def test_submit_passes_draft_to_port_and_returns_number() -> None:
    gh = RecordingGitHub()
    number = IssueService(gh).submit(_bug(), MEMBER)
    assert number == 101
    assert len(gh.created) == 1
    assert gh.created[0].labels == ["bug", "priority:P2"]
