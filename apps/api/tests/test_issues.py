from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_member_service
from src.main import app
from src.models.member_verify import MemberVerify
from src.services.member import MemberPort, MemberService


class FakeMemberPort(MemberPort):
    def __init__(self, registered: dict[str, MemberVerify]) -> None:
        self._registered = registered

    def verify(self, email: str) -> MemberVerify | None:
        return self._registered.get(email.strip().lower())


@pytest.fixture
def client() -> TestClient:
    member = MemberVerify(email="jy_kim@sizl.co.kr", name="김정연", team="Neo Lab")
    fake = FakeMemberPort({"jy_kim@sizl.co.kr": member})
    app.dependency_overrides[get_member_service] = lambda: MemberService(fake)
    yield TestClient(app)
    app.dependency_overrides.clear()


def _bug_payload(email: str) -> dict[str, str]:
    return {
        "tester_email": email,
        "area": "Search",
        "severity": "P2",
        "test_environment": "macOS / Chrome",
        "description": "검색 결과가 비어 있음",
        "reproduction_steps": "1. 검색 2. 엔터",
    }


def _enhancement_payload(email: str) -> dict[str, str]:
    return {
        "tester_email": email,
        "area": "Dashboard",
        "description": "팀별 필터 요청",
        "expected_behavior": "우측 상단 필터 노출",
    }


def test_registered_bug_returns_200(client: TestClient) -> None:
    res = client.post("/issues", json=_bug_payload("jy_kim@sizl.co.kr"))
    assert res.status_code == 200
    body = res.json()
    assert body == {
        "status": "accepted",
        "kind": "bug",
        "email": "jy_kim@sizl.co.kr",
        "name": "김정연",
        "team": "Neo Lab",
    }


def test_registered_enhancement_returns_200(client: TestClient) -> None:
    res = client.post("/issues", json=_enhancement_payload("JY_KIM@sizl.co.kr"))
    assert res.status_code == 200
    assert res.json()["kind"] == "enhancement"


def test_unregistered_returns_403(client: TestClient) -> None:
    res = client.post("/issues", json=_bug_payload("nobody@sizl.co.kr"))
    assert res.status_code == 403
    assert "등록되지 않은" in res.json()["detail"]


def test_invalid_payload_returns_422(client: TestClient) -> None:
    # severity 누락 + reproduction_steps 누락 → bug로도 enhancement로도 검증 실패.
    res = client.post("/issues", json={"tester_email": "jy_kim@sizl.co.kr", "area": "X"})
    assert res.status_code == 422
