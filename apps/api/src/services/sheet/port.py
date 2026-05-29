from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal


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
        """버그(Raw Issues 탭) 행의 처리 상태(+ PR 번호/링크, + '조치 내용')를 갱신.

        action_text 가 주어지면 '조치 내용' 컬럼에 기록한다.
        (CLAUDE.md 운영자 컬럼 보호 규칙 예외 — 사용자 결정: PR close 시 자동 코멘트
        텍스트를 시트에도 미러링. 운영자가 이후 덮어쓸 수 있음.)
        """
        ...

    @abstractmethod
    def update_enhancement_status(
        self,
        issue_number: int,
        status: str,
        action_text: str | None = None,
    ) -> None:
        """개선(Enhancement 탭) 행의 처리 상태(+ '조치 내용')를 갱신.

        GitHub 이슈가 closed 되면 webhook 이 호출 — state_reason 으로
        '검토완료 · 반영' / '검토완료 · 미반영' 매핑.
        """
        ...

    @abstractmethod
    def next_issue_id(self, kind: Literal["bug", "enhancement"]) -> str:
        """다음 Issue ID 생성. bug→BUG-NNN / enhancement→REQ-NNN.

        해당 탭의 'Issue ID' 컬럼 마지막 값 보고 +1. 비어있으면 001.
        race condition 가능하지만 베타 규모에서 무시 (ADR 2026-05-29).
        """
        ...
