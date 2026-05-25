from __future__ import annotations

from src.adapters.ports.issue_port import IssuePort
from src.models.bug_report import BugReport
from src.models.enhancement_request import EnhancementRequest


class DummyIssueAdapter(IssuePort):
    def submit(self, report: BugReport | EnhancementRequest) -> int:
        raise NotImplementedError("W2에서 구현")
