from __future__ import annotations

from src.models.bug_report import BugReport
from src.models.enhancement_request import EnhancementRequest
from src.services.issue.port import IssuePort


class DummyIssueAdapter(IssuePort):
    def submit(self, report: BugReport | EnhancementRequest) -> int:
        raise NotImplementedError("W2에서 구현")
