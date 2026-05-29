from __future__ import annotations

from src.core.logging import logger
from src.models.analysis_result import AnalysisResult
from src.models.bug_report import BugReport
from src.services.llm.port import IssueOpenContext, LLMPort, PRCloseContext


class FallbackLLMAdapter(LLMPort):
    """Primary LLM 호출 → None/실패 시 Secondary 호출. LLM-agnostic 체인.

    각 어댑터(Anthropic/Gemini)는 이미 내부에서 예외를 잡아 None 으로 반환하므로
    여기서는 단순히 'primary 결과가 None 이면 secondary 시도' 로 충분.

    사용 예: FallbackLLMAdapter(primary=AnthropicAdapter, secondary=GeminiAdapter)
    → Claude rate limit / quota / network error 시 Gemini 로 자동 우회.
    """

    def __init__(self, primary: LLMPort, secondary: LLMPort) -> None:
        self._primary = primary
        self._secondary = secondary

    def analyze(self, bug_report: BugReport) -> AnalysisResult:
        # analyze 는 throw 시그니처라 fallback 적용. NotImplementedError 도 fallback.
        try:
            return self._primary.analyze(bug_report)
        except Exception as exc:  # noqa: BLE001
            logger.warning("llm_analyze_fallback", primary_error=str(exc))
            return self._secondary.analyze(bug_report)

    def is_healthy(self) -> bool:
        # 둘 중 하나라도 정상이면 healthy.
        return self._primary.is_healthy() or self._secondary.is_healthy()

    def summarize_pr_close(self, ctx: PRCloseContext) -> str | None:
        result = self._primary.summarize_pr_close(ctx)
        if result is not None:
            return result
        logger.info("llm_close_fallback_to_secondary", issue=ctx.issue_number)
        return self._secondary.summarize_pr_close(ctx)

    def draft_pr_body(self, ctx: IssueOpenContext) -> str | None:
        result = self._primary.draft_pr_body(ctx)
        if result is not None:
            return result
        logger.info("llm_pr_body_fallback_to_secondary", issue=ctx.issue_number)
        return self._secondary.draft_pr_body(ctx)
