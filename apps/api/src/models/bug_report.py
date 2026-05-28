from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel

from src.models.attachment import AttachmentInput


class Severity(StrEnum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class BugReport(BaseModel):
    """버그 신고 폼 페이로드 (웹 폼과 1:1).

    프론트는 camelCase(screenUrl 등)로 보내고, populate_by_name=True 이므로
    서버 코드는 snake_case 필드명으로 접근한다. reporter_email은 로그인 이메일로
    Members.xlsx 검증에 쓰이고, test_account는 테스트 대상 시스템 계정(선택, QA 정보).
    상세 필드(재현단계/예상·실제/입출력/환경 등)는 GitHub 이슈 본문에 들어가며,
    시트에는 요약 컬럼만 기록한다.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )

    reporter_email: EmailStr  # 로그인 이메일 (Members 검증)
    title: str = Field(min_length=1)  # 이슈 제목 (필수, GitHub/시트/목록 표시용)
    test_account: str | None = None  # 테스트 계정 (선택, QA)
    screen_url: str = Field(min_length=1)  # 발생 화면 URL (필수)
    access_time: str | None = None
    area: str = Field(min_length=1)
    severity: Severity
    # 테스트 환경 (자동 감지, 선택)
    os: str | None = None
    browser: str | None = None
    device: str | None = None
    network: str | None = None
    # 시나리오 / 재현 / 동작 / 값
    detailed_feature: str | None = None
    scenario_description: str | None = None
    frequency: str | None = None
    reproduction_steps: list[str] = Field(default_factory=list)
    expected_behavior: str | None = None
    actual_behavior: str | None = None
    input_value: str | None = None
    actual_output: str | None = None
    expected_output: str | None = None
    additional_comments: str | None = None
    error_log: str | None = None
    attachments: list[AttachmentInput] = Field(default_factory=list)
