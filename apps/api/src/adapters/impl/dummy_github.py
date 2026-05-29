from __future__ import annotations

from src.models.issue_draft import IssueDraft
from src.services.github.port import GitHubPort


class DummyGitHubAdapter(GitHubPort):
    def create_issue(self, draft: IssueDraft) -> int:
        raise NotImplementedError("W2에서 구현")

    def get_issue(self, issue_number: int) -> dict[str, str]:
        raise NotImplementedError("W2에서 구현")

    def list_issue_titles(self) -> dict[int, str]:
        raise NotImplementedError("W2에서 구현")

    def update_issue(self, issue_number: int, title: str, body: str) -> None:
        raise NotImplementedError("W2에서 구현")

    def add_comment(self, issue_number: int, body: str) -> None:
        raise NotImplementedError("W2에서 구현")

    def create_empty_pr(self, issue_number: int, title: str, body: str) -> int:
        raise NotImplementedError("W2에서 구현")

    def upload_image(self, filename: str, content: bytes) -> str:
        raise NotImplementedError("W2에서 구현")

    def close_issue(self, issue_number: int, state_reason: str | None = None) -> None:
        raise NotImplementedError("W2에서 구현")

    def close_pr_for_issue(self, issue_number: int) -> int | None:
        raise NotImplementedError("W2에서 구현")
