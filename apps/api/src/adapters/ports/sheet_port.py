from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.member_verify import MemberVerify


class SheetPort(ABC):
    @abstractmethod
    def append_issue(self, issue: dict) -> None: ...

    @abstractmethod
    def verify_member(self, email: str) -> MemberVerify | None: ...

    @abstractmethod
    def update_pr_status(self, issue_number: int, status: str) -> None: ...
