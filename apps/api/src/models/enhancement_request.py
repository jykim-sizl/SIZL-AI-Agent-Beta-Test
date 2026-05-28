from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel

from src.models.attachment import AttachmentInput


class Priority(StrEnum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class EnhancementRequest(BaseModel):
    """개선 의견 폼 페이로드 (웹 폼과 1:1).

    버그와 동일하게 camelCase 별칭을 수용하고, reporter_email로 검증한다.
    개선은 재현/원인 개념이 없고, 우선순위는 버그 심각도와 동일하게 P1~P4.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )

    reporter_email: EmailStr  # 로그인 이메일 (Members 검증)
    title: str = Field(min_length=1)  # 이슈 제목 (필수, GitHub/시트/목록 표시용)
    test_account: str | None = None  # 테스트 계정 (선택)
    screen_url: str = Field(min_length=1)  # 관련 화면 URL (필수)
    area: str = Field(min_length=1)
    priority: Priority
    os: str | None = None
    browser: str | None = None
    device: str | None = None
    network: str | None = None
    feature_to_improve: str = Field(min_length=1)
    current_behavior: str | None = None
    expected_behavior: str | None = None
    rationale: str | None = None
    additional_comments: str | None = None
    attachments: list[AttachmentInput] = Field(default_factory=list)
