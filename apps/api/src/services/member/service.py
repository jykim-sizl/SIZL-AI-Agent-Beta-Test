from __future__ import annotations

from src.core.exceptions import MemberNotRegisteredError
from src.models.member_verify import MemberVerify
from src.services.member.port import MemberPort


class MemberService:
    """회원 검증 비즈니스 로직. ABC(MemberPort)에만 의존한다.

    모든 폼 제출의 첫 관문이며, 다른 부수효과 이전에 가장 먼저 실행되어야 한다.
    미등재 이메일은 MemberNotRegisteredError로 거부한다 (라우트에서 403으로 매핑).
    """

    def __init__(self, members: MemberPort) -> None:
        self._members = members

    def verify(self, email: str) -> MemberVerify:
        member = self._members.verify(email)
        if member is None:
            raise MemberNotRegisteredError(email)
        return member
