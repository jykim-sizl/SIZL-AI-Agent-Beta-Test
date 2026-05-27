from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # GitHub
    github_app_id: str
    github_app_private_key_path: str
    github_webhook_secret: str
    # 이슈는 App이 설치된 이 repo에 생성, PR은 공동 repo(target)에 생성 (CLAUDE.md)
    github_issue_repo: str = "jykim-sizl/SIZL-AI-Agent-Beta-Test"
    github_target_repo: str = "Sizl-Neolab/SIZL-Agentic-Brain-Issue-Track"

    # Anthropic
    anthropic_api_key: str

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
