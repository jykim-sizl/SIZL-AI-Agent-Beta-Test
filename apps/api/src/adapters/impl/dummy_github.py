from __future__ import annotations

from src.models.analysis_result import AnalysisResult
from src.models.issue_draft import IssueDraft
from src.services.github.port import GitHubPort


class DummyGitHubAdapter(GitHubPort):
    def create_issue(self, draft: IssueDraft) -> int:
        raise NotImplementedError("W2에서 구현")

    def create_empty_pr(self, issue_number: int, analysis: AnalysisResult) -> int:
        raise NotImplementedError("W2에서 구현")

    def close_issue(self, issue_number: int) -> None:
        raise NotImplementedError("W2에서 구현")
