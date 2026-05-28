from __future__ import annotations

from src.models.analysis_result import AnalysisResult
from src.models.bug_report import BugReport
from src.services.llm.port import LLMPort, PRCloseContext


class DummyLLMAdapter(LLMPort):
    """LLM 키 없을 때의 fallback. summarize_pr_close 는 None 을 돌려 호출자가 템플릿 사용."""

    def analyze(self, bug_report: BugReport) -> AnalysisResult:
        raise NotImplementedError("W2에서 구현")

    def is_healthy(self) -> bool:
        return False

    def summarize_pr_close(self, ctx: PRCloseContext) -> str | None:
        return None
