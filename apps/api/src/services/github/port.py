from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.issue_draft import IssueDraft


class GitHubPort(ABC):
    @abstractmethod
    def create_issue(self, draft: IssueDraft) -> int:
        """완성된 IssueDraft(title/body/labels)로 GitHub Issue를 만들고 번호를 반환."""
        ...

    @abstractmethod
    def get_issue(self, issue_number: int) -> dict[str, str]:
        """이슈의 현재 title/body 반환 (수정 모달 prefill 용)."""
        ...

    @abstractmethod
    def list_issue_titles(self) -> dict[int, str]:
        """{issue_number: title} 일괄 조회. 목록 표시용 — 최근 N개만."""
        ...

    @abstractmethod
    def update_issue(self, issue_number: int, title: str, body: str) -> None:
        """이슈의 title/body 갱신."""
        ...

    @abstractmethod
    def add_comment(self, issue_number: int, body: str) -> None:
        """이슈에 댓글 추가 (사용자가 남긴 '추가 의견' 용)."""
        ...

    @abstractmethod
    def create_empty_pr(self, issue_number: int, title: str, body: str) -> int:
        """이슈용 빈 브랜치 + 빈 PR(코드 없음)을 만들고 PR 번호를 반환.

        body에는 러프 안내가 들어가며, Playwright 재현 요약 / LLM 원인가설은
        후속 단계에서 본문을 채워 넣는다(현재는 자리만).
        """
        ...

    @abstractmethod
    def upload_image(self, filename: str, content: bytes) -> str:
        """이미지를 공개 repo에 올리고 이슈 본문에 넣을 raw URL을 반환."""
        ...

    @abstractmethod
    def close_issue(self, issue_number: int) -> None: ...
