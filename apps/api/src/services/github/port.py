from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.analysis_result import AnalysisResult
from src.models.bug_report import BugReport
from src.models.enhancement_request import EnhancementRequest


class GitHubPort(ABC):
    @abstractmethod
    def create_issue(self, report: BugReport | EnhancementRequest) -> int: ...

    @abstractmethod
    def create_empty_pr(self, issue_number: int, analysis: AnalysisResult) -> int: ...

    @abstractmethod
    def close_issue(self, issue_number: int) -> None: ...
