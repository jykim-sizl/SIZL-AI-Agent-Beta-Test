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

    def add(self, member: MemberVerify) -> None:
        self._registered[member.email.strip().lower()] = member


@pytest.fixture
def client() -> TestClient:
    member = MemberVerify(email="jy_kim@sizl.co.kr", name="김정연", team="Neo Lab")
    fake = FakeMemberPort({"jy_kim@sizl.co.kr": member})
    app.dependency_overrides[get_member_service] = lambda: MemberService(fake)
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_verify_registered_returns_member(client: TestClient) -> None:
    res = client.post("/members/verify", json={"email": "jy_kim@sizl.co.kr"})
    assert res.status_code == 200
    assert res.json() == {"email": "jy_kim@sizl.co.kr", "name": "김정연", "team": "Neo Lab"}


def test_verify_normalizes_case(client: TestClient) -> None:
    res = client.post("/members/verify", json={"email": "JY_KIM@sizl.co.kr"})
    assert res.status_code == 200


def test_verify_unregistered_returns_403(client: TestClient) -> None:
    res = client.post("/members/verify", json={"email": "nobody@external.com"})
    assert res.status_code == 403
    assert "등록되지 않은" in res.json()["detail"]


def test_register_adds_member_then_verifies(client: TestClient) -> None:
    # 미등록자가 등록 → 이후 verify 통과
    new = {"name": "신규자", "team": "QA", "email": "newbie@sizl.co.kr"}
    res = client.post("/members/register", json=new)
    assert res.status_code == 200
    assert res.json() == {"email": "newbie@sizl.co.kr", "name": "신규자", "team": "QA"}

    res2 = client.post("/members/verify", json={"email": "newbie@sizl.co.kr"})
    assert res2.status_code == 200
