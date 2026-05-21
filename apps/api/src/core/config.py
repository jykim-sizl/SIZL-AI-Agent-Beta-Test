from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # GitHub
    github_app_id: str
    github_app_private_key_path: str
    github_webhook_secret: str
    github_target_repo: str = "Sizl-Neolab/SIZL-Agentic-Brain-Issue-Track"

    # Anthropic
    anthropic_api_key: str

    # Google Sheets
    google_service_account_json_path: str
    google_spreadsheet_id: str

    # Slack
    slack_webhook_url: str

    # App
    app_env: str = "development"
    log_level: str = "INFO"


settings = Settings()  # type: ignore[call-arg]
