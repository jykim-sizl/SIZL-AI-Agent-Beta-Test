from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.analysis_result import AnalysisResult
from src.models.issue_draft import IssueDraft


class GitHubPort(ABC):
    @abstractmethod
    def create_issue(self, draft: IssueDraft) -> int:
        """완성된 IssueDraft(title/body/labels)로 GitHub Issue를 만들고 번호를 반환."""
        ...

    @abstractmethod
    def create_empty_pr(self, issue_number: int, analysis: AnalysisResult) -> int: ...

    @abstractmethod
    def close_issue(self, issue_number: int) -> None: ...
