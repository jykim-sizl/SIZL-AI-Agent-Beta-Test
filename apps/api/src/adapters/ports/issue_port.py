from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.bug_report import BugReport
from src.models.enhancement_request import EnhancementRequest


class IssuePort(ABC):
    @abstractmethod
    def submit(self, report: BugReport | EnhancementRequest) -> int: ...
