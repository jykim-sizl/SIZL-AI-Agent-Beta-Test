from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EnhancementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    tester_email: EmailStr
    area: str = Field(min_length=1)
    description: str = Field(min_length=1)
    expected_behavior: str = Field(min_length=1)
