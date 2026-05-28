import hashlib
import hmac
import json
from typing import Any

import pytest
from fastapi.testclient import TestClient
from structlog.testing import capture_logs

from src.api.deps import get_pr_service, get_sheet
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
        self.status: list[tuple[int, str]] = []

    def append_bug(self, row: dict[str, Any]) -> None:  # pragma: no cover
        pass

    def append_enhancement(self, row: dict[str, Any]) -> None:  # pragma: no cover
        pass

    def update_pr_status(self, issue_number: int, status: str) -> None:
        self.status.append((issue_number, status))


@pytest.fixture
def fakes() -> tuple[FakePR, FakeSheet]:
    pr, sheet = FakePR(), FakeSheet()
    app.dependency_overrides[get_pr_service] = lambda: pr
    app.dependency_overrides[get_sheet] = lambda: sheet
    yield pr, sheet
    app.dependency_overrides.clear()


@pytest.fixture
def client(fakes: tuple[FakePR, FakeSheet]) -> TestClient:
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
def test_bug_issue_opened_triggers_pr(client: TestClient, fakes: tuple[FakePR, FakeSheet]) -> None:
    pr, _ = fakes
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
    client: TestClient, fakes: tuple[FakePR, FakeSheet]
) -> None:
    pr, _ = fakes
    payload = {
        "action": "opened",
        "issue": {"number": 43, "title": "개선", "labels": [{"name": "enhancement"}]},
    }
    assert _post(client, payload, "issues").status_code == 200
    assert pr.created == []


def test_p4_bug_also_triggers_pr(client: TestClient, fakes: tuple[FakePR, FakeSheet]) -> None:
    # 사용자 결정(2026-05-27): P4 버그도 PR 생성.
    pr, _ = fakes
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


def test_pr_merged_updates_sheet(client: TestClient, fakes: tuple[FakePR, FakeSheet]) -> None:
    _, sheet = fakes
    payload = {
        "action": "closed",
        "pull_request": {"merged": True, "head": {"ref": "auto/issue-42"}},
    }
    assert _post(client, payload, "pull_request").status_code == 200
    assert sheet.status == [(42, "완료")]


def test_pr_closed_not_merged_no_update(
    client: TestClient, fakes: tuple[FakePR, FakeSheet]
) -> None:
    _, sheet = fakes
    payload = {
        "action": "closed",
        "pull_request": {"merged": False, "head": {"ref": "auto/issue-42"}},
    }
    assert _post(client, payload, "pull_request").status_code == 200
    assert sheet.status == []


def test_verify_function_unit() -> None:
    body = b"payload"
    assert verify_github_signature(body, _sign(body), SECRET) is True
    assert verify_github_signature(body, _sign(body, "wrong-secret"), SECRET) is False
    assert verify_github_signature(body, None, SECRET) is False
    assert verify_github_signature(body, "deadbeef", SECRET) is False
