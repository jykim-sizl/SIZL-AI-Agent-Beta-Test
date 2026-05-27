from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MemberVerify(BaseModel):
    """Members.xlsx 1행에 대응하는 검증된 회원.

    베타 기간 Members.xlsx는 이름/이메일/팀 3컬럼뿐이며 활성 여부 컬럼이 없다.
    따라서 "파일에 등재됨 = 검증 통과"로 다루고 is_active 개념은 두지 않는다.
    미등재 이메일은 MemberPort가 None을 반환하고, 403 변환은 서비스 계층 책임.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: EmailStr
    name: str = Field(min_length=1)
    team: str = Field(min_length=1)
