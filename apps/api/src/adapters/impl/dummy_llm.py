from __future__ import annotations

from src.adapters.ports.llm_port import LLMPort
from src.models.analysis_result import AnalysisResult
from src.models.bug_report import BugReport


class DummyLLMAdapter(LLMPort):
    def analyze(self, bug_report: BugReport) -> AnalysisResult:
        raise NotImplementedError("W2에서 구현")

    def is_healthy(self) -> bool:
        raise NotImplementedError("W2에서 구현")
