from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.api.deps import get_github, get_issue_service, get_member_service, get_sheet
from src.main import app
from src.models.issue_draft import IssueDraft
from src.models.member_verify import MemberVerify
from src.services.github import GitHubPort
from src.services.issue import IssueService
from src.services.member import MemberPort, MemberService
from src.services.sheet import SheetPort


class FakeMemberPort(MemberPort):
    def __init__(self, registered: dict[str, MemberVerify]) -> None:
        self._registered = registered

    def verify(self, email: str) -> MemberVerify | None:
        return self._registered.get(email.strip().lower())

    def add(self, member: MemberVerify) -> None:  # pragma: no cover
        self._registered[member.email.strip().lower()] = member


class FakeGitHub(GitHubPort):
    """이슈 생성·조회·갱신·댓글을 메모리에 기록하는 테스트용 GitHubPort."""

    def __init__(self) -> None:
        # 기본: 이슈 #101 이 이미 있는 셈 치고 get/update 테스트에 쓰임.
        self.issues: dict[int, dict[str, str]] = {101: {"title": "원래 제목", "body": "원래 본문"}}
        self.comments: list[tuple[int, str]] = []

    def create_issue(self, draft: IssueDraft) -> int:
        self.issues[101] = {"title": draft.title, "body": draft.body}
        return 101

    def get_issue(self, issue_number: int) -> dict[str, str]:
        return self.issues[issue_number]

    def update_issue(self, issue_number: int, title: str, body: str) -> None:
        self.issues[issue_number] = {"title": title, "body": body}

    def add_comment(self, issue_number: int, body: str) -> None:
        self.comments.append((issue_number, body))

    def list_issue_titles(self) -> dict[int, str]:
        return {n: i["title"] for n, i in self.issues.items()}

    def create_empty_pr(self, issue_number: int, title: str, body: str) -> int:  # pragma: no cover
        raise NotImplementedError

    def upload_image(self, filename: str, content: bytes) -> str:  # pragma: no cover
        return f"https://example.com/{filename}"

    def close_issue(
        self, issue_number: int, state_reason: str | None = None
    ) -> None:  # pragma: no cover
        raise NotImplementedError


class FakeSheet(SheetPort):
    """append 호출을 기록하는 테스트용 SheetPort (실 시트 미호출)."""

    def __init__(self) -> None:
        self.bugs: list[dict[str, Any]] = []
        self.enhancements: list[dict[str, Any]] = []

    def append_bug(self, row: dict[str, Any]) -> None:
        self.bugs.append(row)

    def append_enhancement(self, row: dict[str, Any]) -> None:
        self.enhancements.append(row)

    def list_issues(self) -> list[dict[str, Any]]:  # pragma: no cover
        return []

    def update_enhancement_status(  # pragma: no cover
        self,
        issue_number: int,
        status: str,
        action_text: str | None = None,
    ) -> None:
        raise NotImplementedError

    def update_pr_status(  # pragma: no cover
        self,
        issue_number: int,
        status: str,
        pr_number: int | None = None,
        pr_url: str | None = None,
        action_text: str | None = None,
    ) -> None:
        raise NotImplementedError


@pytest.fixture
def sheet() -> FakeSheet:
    return FakeSheet()


@pytest.fixture
def client(sheet: FakeSheet) -> TestClient:
    member = MemberVerify(email="jy_kim@sizl.co.kr", name="김정연", team="Neo Lab")
    fake = FakeMemberPort({"jy_kim@sizl.co.kr": member})
    gh = FakeGitHub()
    app.dependency_overrides[get_member_service] = lambda: MemberService(fake)
    app.dependency_overrides[get_issue_service] = lambda: IssueService(gh)
    app.dependency_overrides[get_sheet] = lambda: sheet
    # GET /issues 가 GitHub 제목 fetch 하므로 override (실 API 호출 방지).
    app.dependency_overrides[get_github] = lambda: gh
    yield TestClient(app)
    app.dependency_overrides.clear()


def _bug_payload(email: str) -> dict[str, object]:
    # 프론트가 보내는 camelCase 페이로드 형태.
    return {
        "title": "제목 테스트",
        "reporterEmail": email,
        "screenUrl": "https://app.example.com/search",
        "area": "Search",
        "severity": "P2",
        "actualBehavior": "검색 결과가 비어 있음",
        "reproductionSteps": ["검색", "엔터"],
    }


def _enhancement_payload(email: str) -> dict[str, object]:
    return {
        "title": "제목 테스트",
        "reporterEmail": email,
        "screenUrl": "https://app.example.com/dashboard",
        "area": "Dashboard",
        "priority": "P3",
        "featureToImprove": "팀별 필터 요청",
        "expectedBehavior": "우측 상단 필터 노출",
    }


def test_registered_bug_returns_200_and_appends_sheet(client: TestClient, sheet: FakeSheet) -> None:
    res = client.post("/issues", json=_bug_payload("jy_kim@sizl.co.kr"))
    assert res.status_code == 200
    assert res.json() == {
        "status": "accepted",
        "kind": "bug",
        "issue_number": 101,
        "email": "jy_kim@sizl.co.kr",
        "name": "김정연",
        "team": "Neo Lab",
    }
    # 시트 버그 탭에 1건 기록 (자동 컬럼), 운영자 컬럼은 미포함
    assert len(sheet.bugs) == 1
    assert sheet.bugs[0]["# github issue"] == "#101"
    assert "원인 유형" not in sheet.bugs[0]


def test_registered_enhancement_returns_200(client: TestClient, sheet: FakeSheet) -> None:
    res = client.post("/issues", json=_enhancement_payload("JY_KIM@sizl.co.kr"))
    assert res.status_code == 200
    assert res.json()["kind"] == "enhancement"
    assert len(sheet.enhancements) == 1


def test_list_issues_returns_list(client: TestClient) -> None:
    res = client.get("/issues")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_unregistered_returns_403(client: TestClient) -> None:
    res = client.post("/issues", json=_bug_payload("nobody@sizl.co.kr"))
    assert res.status_code == 403
    assert "등록되지 않은" in res.json()["detail"]


def test_invalid_payload_returns_422(client: TestClient) -> None:
    # screenUrl·severity·priority 등 필수 누락 → bug로도 enhancement로도 검증 실패.
    res = client.post("/issues", json={"reporterEmail": "jy_kim@sizl.co.kr", "area": "X"})
    assert res.status_code == 422
