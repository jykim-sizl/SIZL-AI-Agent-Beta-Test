from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MemberVerify(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: EmailStr
    name: str = Field(min_length=1)
    team: str = Field(min_length=1)
    position: str | None = None
    is_active: bool

    def is_eligible(self) -> bool:
        return self.is_active
