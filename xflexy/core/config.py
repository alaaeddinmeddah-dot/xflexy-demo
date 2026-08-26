from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "xflexy"
    environment: str = "local"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./xflexy.db"
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    flexy_provider: str = "mock"
    admin_api_key: str = "change-me-local-admin-key"
    min_flexy_amount: int = 50
    max_flexy_amount: int = 50000
    phone_regex: str = r"^\+?[0-9]{8,15}$"
    mock_flexy_mode: str = "success"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
