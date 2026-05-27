from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.member_verify import MemberVerify


class MemberPort(ABC):
    """회원 검증 계약.

    ADR-001 / PRD v4.0: Members 검증은 Google Sheet가 아니라 로컬 Members.xlsx 기반.
    이메일 정규화(strip + 소문자)는 어댑터 책임이다. 미등재 이메일은 None을 반환하며,
    403(Forbidden) 변환 같은 HTTP 관심사는 서비스 계층이 처리한다.
    """

    @abstractmethod
    def verify(self, email: str) -> MemberVerify | None: ...
