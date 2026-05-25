from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.analysis_result import AnalysisResult
from src.models.bug_report import BugReport


class LLMPort(ABC):
    @abstractmethod
    def analyze(self, bug_report: BugReport) -> AnalysisResult: ...

    @abstractmethod
    def is_healthy(self) -> bool: ...
