import hashlib
import hmac
import json
from typing import Any

import pytest
from fastapi.testclient import TestClient
from structlog.testing import capture_logs

from src.api.deps import get_github, get_pr_service, get_sheet
from src.core.security import verify_github_signature
from src.main import app

SECRET = "test-secret"  # tests/conftest.py의 GITHUB_WEBHOOK_SECRET와 일치


class FakePR:
    def __init__(self) -> None:
        self.created: list[tuple[int, str]] = []

    def create_for_bug(self, issue_number: int, issue_title: str) -> int:
        self.created.append((issue_number, issue_title))
        return 999


class FakeSheet:
    def __init__(self) -> None:
        # (issue_number, status, action_text)
        self.status: list[tuple[int, str, str | None]] = []

    def append_bug(self, row: dict[str, Any]) -> None:  # pragma: no cover
        pass

    def append_enhancement(self, row: dict[str, Any]) -> None:  # pragma: no cover
        pass

    def update_pr_status(
        self,
        issue_number: int,
        status: str,
        pr_number: int | None = None,
        pr_url: str | None = None,
        action_text: str | None = None,
    ) -> None:
        self.status.append((issue_number, status, action_text))

    def update_enhancement_status(
        self,
        issue_number: int,
        status: str,
        action_text: str | None = None,
    ) -> None:
        self.status.append((issue_number, status, action_text))


class FakeGitHub:
    def __init__(self) -> None:
        self.comments: list[tuple[int, str]] = []
        self.closed: list[int] = []

    def add_comment(self, issue_number: int, body: str) -> None:
        self.comments.append((issue_number, body))

    def close_issue(self, issue_number: int) -> None:
        self.closed.append(issue_number)


@pytest.fixture
def fakes() -> tuple[FakePR, FakeSheet, FakeGitHub]:
    pr, sheet, gh = FakePR(), FakeSheet(), FakeGitHub()
    app.dependency_overrides[get_pr_service] = lambda: pr
    app.dependency_overrides[get_sheet] = lambda: sheet
    app.dependency_overrides[get_github] = lambda: gh
    yield pr, sheet, gh
    app.dependency_overrides.clear()


@pytest.fixture
def client(fakes: tuple[FakePR, FakeSheet, FakeGitHub]) -> TestClient:
    return TestClient(app)


def _sign(body: bytes, secret: str = SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _post(client: TestClient, payload: dict[str, Any], event: str) -> Any:
    body = json.dumps(payload).encode()
    return client.post(
        "/webhooks",
        content=body,
        headers={"X-Hub-Signature-256": _sign(body), "X-GitHub-Event": event},
    )


# --- 서명 검증 ---
def test_valid_signature_accepted(client: TestClient) -> None:
    body = b'{"zen":"hello","hook_id":1}'
    resp = client.post("/webhooks", content=body, headers={"X-Hub-Signature-256": _sign(body)})
    assert resp.status_code == 200
    assert resp.json() == {"status": "received"}


def test_invalid_signature_rejected(client: TestClient) -> None:
    body = b'{"zen":"hello"}'
    resp = client.post(
        "/webhooks", content=body, headers={"X-Hub-Signature-256": "sha256=" + "0" * 64}
    )
    assert resp.status_code == 401


def test_missing_signature_rejected(client: TestClient) -> None:
    assert client.post("/webhooks", content=b"{}").status_code == 401


def test_tampered_body_rejected(client: TestClient) -> None:
    sig = _sign(b'{"a":1}')
    resp = client.post("/webhooks", content=b'{"a":2}', headers={"X-Hub-Signature-256": sig})
    assert resp.status_code == 401


def test_event_extracted_and_logged(client: TestClient) -> None:
    body = b'{"action":"opened","issue":{"number":7}}'
    with capture_logs() as logs:
        resp = client.post(
            "/webhooks",
            content=body,
            headers={
                "X-Hub-Signature-256": _sign(body),
                "X-GitHub-Event": "issues",
                "X-GitHub-Delivery": "d-123",
            },
        )
    assert resp.status_code == 200
    entry = next(e for e in logs if e["event"] == "github_webhook_received")
    assert entry["event_type"] == "issues"
    assert entry["action"] == "opened"


# --- 라우팅 ---
def test_bug_issue_opened_triggers_pr(
    client: TestClient, fakes: tuple[FakePR, FakeSheet, FakeGitHub]
) -> None:
    pr, *_ = fakes
    payload = {
        "action": "opened",
        "issue": {
            "number": 42,
            "title": "버그",
            "labels": [{"name": "bug"}, {"name": "priority:P2"}],
        },
    }
    assert _post(client, payload, "issues").status_code == 200
    assert pr.created == [(42, "버그")]


def test_enhancement_issue_opened_no_pr(
    client: TestClient, fakes: tuple[FakePR, FakeSheet, FakeGitHub]
) -> None:
    pr, *_ = fakes
    payload = {
        "action": "opened",
        "issue": {"number": 43, "title": "개선", "labels": [{"name": "enhancement"}]},
    }
    assert _post(client, payload, "issues").status_code == 200
    assert pr.created == []


def test_p4_bug_also_triggers_pr(
    client: TestClient, fakes: tuple[FakePR, FakeSheet, FakeGitHub]
) -> None:
    # 사용자 결정(2026-05-27): P4 버그도 PR 생성.
    pr, *_ = fakes
    payload = {
        "action": "opened",
        "issue": {
            "number": 44,
            "title": "사소",
            "labels": [{"name": "bug"}, {"name": "priority:P4"}],
        },
    }
    assert _post(client, payload, "issues").status_code == 200
    assert pr.created == [(44, "사소")]


def test_pr_merged_updates_sheet(
    client: TestClient, fakes: tuple[FakePR, FakeSheet, FakeGitHub]
) -> None:
    _, sheet, gh = fakes
    payload = {
        "action": "closed",
        "pull_request": {
            "merged": True,
            "number": 7,
            "html_url": "https://github.com/x/y/pull/7",
            "merge_commit_sha": "abcdef1234567890",
            "head": {"ref": "auto/issue-42"},
        },
    }
    assert _post(client, payload, "pull_request").status_code == 200
    # 시트: 상태 '완료' + 코멘트 텍스트가 action_text 로 미러됨
    assert len(sheet.status) == 1
    issue_n, status, action = sheet.status[0]
    assert (issue_n, status) == (42, "완료")
    assert action is not None and "완료" in action and "PR #7" in action
    # 이슈: 코멘트 게시 + close
    assert len(gh.comments) == 1 and gh.comments[0][0] == 42 and "완료" in gh.comments[0][1]
    assert gh.closed == [42]


def test_pr_closed_unmerged_marks_withdrawn(
    client: TestClient, fakes: tuple[FakePR, FakeSheet, FakeGitHub]
) -> None:
    # 머지 없이 닫힌 분석 PR → 이슈 '철회' + 코멘트 + close (사용자 결정 2026-05-28).
    _, sheet, gh = fakes
    payload = {
        "action": "closed",
        "pull_request": {
            "merged": False,
            "number": 8,
            "html_url": "https://github.com/x/y/pull/8",
            "head": {"ref": "auto/issue-42"},
        },
    }
    assert _post(client, payload, "pull_request").status_code == 200
    assert len(sheet.status) == 1
    issue_n, status, action = sheet.status[0]
    assert (issue_n, status) == (42, "철회")
    assert action is not None and "철회" in action
    assert len(gh.comments) == 1 and "철회" in gh.comments[0][1]
    assert gh.closed == [42]


def test_enhancement_closed_completed_marks_accepted(
    client: TestClient, fakes: tuple[FakePR, FakeSheet, FakeGitHub]
) -> None:
    # GitHub 에서 enhancement 이슈를 'completed' 로 close → 시트 '검토완료 · 반영'
    _, sheet, _ = fakes
    payload = {
        "action": "closed",
        "issue": {"number": 50, "labels": [{"name": "enhancement"}], "state_reason": "completed"},
    }
    assert _post(client, payload, "issues").status_code == 200
    assert len(sheet.status) == 1
    n, status, action = sheet.status[0]
    assert (n, status) == (50, "검토완료 · 반영")
    assert action is not None and "반영" in action


def test_enhancement_closed_not_planned_marks_rejected(
    client: TestClient, fakes: tuple[FakePR, FakeSheet, FakeGitHub]
) -> None:
    # 'not_planned' 로 close → 시트 '검토완료 · 미반영'
    _, sheet, _ = fakes
    payload = {
        "action": "closed",
        "issue": {
            "number": 51,
            "labels": [{"name": "enhancement"}],
            "state_reason": "not_planned",
        },
    }
    assert _post(client, payload, "issues").status_code == 200
    assert sheet.status[0][:2] == (51, "검토완료 · 미반영")


def test_bug_closed_directly_ignored(
    client: TestClient, fakes: tuple[FakePR, FakeSheet, FakeGitHub]
) -> None:
    # bug 이슈가 (PR 경유 없이) close 되면 이 핸들러는 무시 (PR-close 가 따로 처리).
    _, sheet, _ = fakes
    payload = {
        "action": "closed",
        "issue": {"number": 52, "labels": [{"name": "bug"}], "state_reason": "completed"},
    }
    assert _post(client, payload, "issues").status_code == 200
    assert sheet.status == []


def test_pr_closed_unrelated_branch_ignored(
    client: TestClient, fakes: tuple[FakePR, FakeSheet, FakeGitHub]
) -> None:
    # auto/issue-N 외 브랜치의 PR 은 무시 (수동 PR/외부 PR 등).
    _, sheet, gh = fakes
    payload = {
        "action": "closed",
        "pull_request": {"merged": True, "head": {"ref": "feature/something"}},
    }
    assert _post(client, payload, "pull_request").status_code == 200
    assert sheet.status == []
    assert gh.comments == []
    assert gh.closed == []


def test_verify_function_unit() -> None:
    body = b"payload"
    assert verify_github_signature(body, _sign(body), SECRET) is True
    assert verify_github_signature(body, _sign(body, "wrong-secret"), SECRET) is False
    assert verify_github_signature(body, None, SECRET) is False
    assert verify_github_signature(body, "deadbeef", SECRET) is False
