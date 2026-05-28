from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.models.analysis_result import AnalysisResult
from src.models.bug_report import BugReport


@dataclass(frozen=True)
class PRCloseContext:
    """PR-close 코멘트 풍부화에 필요한 컨텍스트 (LLM-agnostic)."""

    issue_number: int
    issue_title: str
    issue_body: str
    pr_number: int | None
    pr_title: str
    pr_body: str
    pr_url: str
    merged: bool
    merge_commit_sha: str  # 머지된 경우 짧은 SHA, 아니면 빈 문자열


class LLMPort(ABC):
    @abstractmethod
    def analyze(self, bug_report: BugReport) -> AnalysisResult: ...

    @abstractmethod
    def is_healthy(self) -> bool: ...

    @abstractmethod
    def summarize_pr_close(self, ctx: PRCloseContext) -> str | None:
        """PR-close 시 이슈에 달 코멘트의 풍부화된 텍스트.

        반환:
            - 마크다운 문자열: 그대로 이슈 코멘트로 게시
            - None: LLM 호출 불가/실패 → 호출자가 템플릿 fallback
        """
        ...
