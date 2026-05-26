import hashlib
import hmac

from fastapi.testclient import TestClient
from structlog.testing import capture_logs

from src.core.security import verify_github_signature
from src.main import app

SECRET = "test-secret"  # tests/conftest.py의 GITHUB_WEBHOOK_SECRET와 일치
client = TestClient(app)


def _sign(body: bytes, secret: str = SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_valid_signature_accepted() -> None:
    body = b'{"zen":"hello","hook_id":1}'
    resp = client.post("/webhooks", content=body, headers={"X-Hub-Signature-256": _sign(body)})
    assert resp.status_code == 200
    assert resp.json() == {"status": "received"}


def test_invalid_signature_rejected() -> None:
    body = b'{"zen":"hello"}'
    bad = "sha256=" + "0" * 64
    resp = client.post("/webhooks", content=body, headers={"X-Hub-Signature-256": bad})
    assert resp.status_code == 401


def test_missing_signature_rejected() -> None:
    resp = client.post("/webhooks", content=b"{}")
    assert resp.status_code == 401


def test_tampered_body_rejected() -> None:
    # 서명은 원본 body 기준인데 다른 body를 보내면 거부되어야 한다.
    sig = _sign(b'{"a":1}')
    resp = client.post("/webhooks", content=b'{"a":2}', headers={"X-Hub-Signature-256": sig})
    assert resp.status_code == 401


def test_event_extracted_and_logged() -> None:
    # 유효 서명 + issues/opened 이벤트 → 200 수락, 이벤트 종류·action이 로그에 남는다.
    body = b'{"action":"opened","issue":{"number":7}}'
    with capture_logs() as logs:
        resp = client.post(
            "/webhooks",
            content=body,
            headers={
                "X-Hub-Signature-256": _sign(body),
                "X-GitHub-Event": "issues",
                "X-GitHub-Delivery": "delivery-123",
            },
        )
    assert resp.status_code == 200
    entry = next(e for e in logs if e["event"] == "github_webhook_received")
    assert entry["event_type"] == "issues"
    assert entry["action"] == "opened"
    assert entry["delivery"] == "delivery-123"


def test_verify_function_unit() -> None:
    body = b"payload"
    assert verify_github_signature(body, _sign(body), SECRET) is True
    assert verify_github_signature(body, _sign(body, "wrong-secret"), SECRET) is False
    assert verify_github_signature(body, None, SECRET) is False
    assert verify_github_signature(body, "deadbeef", SECRET) is False  # sha256= 접두어 없음
