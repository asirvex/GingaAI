import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = os.getenv(
        "DATABASE_URL", "sqlite+aiosqlite:///./claims.db"
    )
    app_name: str = "Claims Processing Service"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    api_key: str = os.getenv("API_KEY", "dev-test-api-key")


settings = Settings()
