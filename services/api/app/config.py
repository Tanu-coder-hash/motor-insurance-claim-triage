
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "Motor Insurance Claim Triage"
    app_version: str = "1.0.0"
    log_level: str = "INFO"

    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/motor_insurance"
    )

    redis_url: str = "redis://localhost:6379/0"

    rate_limit_per_min: int = 30
    run_cache_ttl_s: int = 3600

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
