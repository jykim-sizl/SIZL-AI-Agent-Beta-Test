from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.issue_draft import IssueDraft


class GitHubPort(ABC):
    @abstractmethod
    def create_issue(self, draft: IssueDraft) -> int:
        """완성된 IssueDraft(title/body/labels)로 GitHub Issue를 만들고 번호를 반환."""
        ...

    @abstractmethod
    def create_empty_pr(self, issue_number: int, title: str, body: str) -> int:
        """이슈용 빈 브랜치 + 빈 PR(코드 없음)을 만들고 PR 번호를 반환.

        body에는 러프 안내가 들어가며, Playwright 재현 요약 / LLM 원인가설은
        후속 단계에서 본문을 채워 넣는다(현재는 자리만).
        """
        ...

    @abstractmethod
    def close_issue(self, issue_number: int) -> None: ...
