from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SheetPort(ABC):
    """Google Sheets 양 시트(Raw Bugs / Raw Enhancements) 갱신 계약.

    ADR-003: 단일 Raw Issues 시트 대신 bug/enhancement를 분리한다.
    Members 조회는 ADR-001·PRD v4.0에 따라 로컬 xlsx 기반이므로
    여기 포함하지 않는다 (TODO: 별도 MemberPort 도입은 W1 후반/W2).
    """

    @abstractmethod
    def append_bug(self, row: dict[str, Any]) -> None: ...

    @abstractmethod
    def append_enhancement(self, row: dict[str, Any]) -> None: ...

    @abstractmethod
    def update_pr_status(self, issue_number: int, status: str) -> None: ...
