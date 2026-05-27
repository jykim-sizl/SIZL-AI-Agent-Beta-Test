from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from src.adapters.impl import ExcelMemberAdapter
from src.core.config import settings
from src.services.member import MemberService


@lru_cache
def _member_service() -> MemberService:
    # 어댑터를 싱글턴으로 재사용해 5분 메모리 캐시(NFR-12)가 요청 간 유지되도록 한다.
    return MemberService(ExcelMemberAdapter(settings.members_xlsx_path))


def get_member_service() -> MemberService:
    return _member_service()


MemberServiceDep = Annotated[MemberService, Depends(get_member_service)]
