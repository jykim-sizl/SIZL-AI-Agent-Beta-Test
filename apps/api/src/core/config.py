from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # GitHub
    github_app_id: str
    github_app_private_key_path: str
    github_webhook_secret: str
    # 이슈는 이 repo에, PR은 App이 설치된 타깃 repo(QA_test)에 생성. (둘 다 App 설치됨)
    github_issue_repo: str = "jykim-sizl/SIZL-AI-Agent-Beta-Test"
    github_target_repo: str = "kimjy-st/QA_test"

    # Anthropic (현재 미사용, 키 발급 대기 — Gemini 로 우선 운영)
    anthropic_api_key: str
    # Gemini (Google AI Studio 무료 tier). 없으면 LLM 호출 없이 템플릿 fallback.
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"

    # Google Sheets
    google_service_account_json_path: str
    google_spreadsheet_id: str

    # Slack
    slack_webhook_url: str

    # Members (로컬 xlsx 검증, ADR-001 / PRD v4.0)
    members_xlsx_path: str = "data/Members.xlsx"

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    # CORS 허용 오리진 (콤마 구분). Phase A 로컬 웹.
    cors_origins: str = "http://localhost:3000"


settings = Settings()  # type: ignore[call-arg]
