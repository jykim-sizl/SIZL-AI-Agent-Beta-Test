from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Severity(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class BugReport(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    tester_email: EmailStr
    tester_name: str | None = None
    area: str = Field(min_length=1)
    severity: Severity
    test_environment: str = Field(min_length=1)
    description: str = Field(min_length=1)
    reproduction_steps: str = Field(min_length=1)
    image_url: str | None = None
