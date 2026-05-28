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
    def list_issues(self) -> list[dict[str, Any]]:
        """Raw Bugs + Enhancements 행을 프론트 목록용 dict 리스트로 반환(읽기 전용)."""
        ...

    @abstractmethod
    def update_pr_status(
        self,
        issue_number: int,
        status: str,
        pr_number: int | None = None,
        pr_url: str | None = None,
        action_text: str | None = None,
    ) -> None:
        """이슈 행의 처리 상태(+ PR 번호/링크, + '조치 내용')를 갱신.

        action_text 가 주어지면 '조치 내용' 컬럼에 기록한다.
        (CLAUDE.md 운영자 컬럼 보호 규칙 예외 — 사용자 결정: PR close 시 자동 코멘트
        텍스트를 시트에도 미러링. 운영자가 이후 덮어쓸 수 있음.)
        """
        ...
