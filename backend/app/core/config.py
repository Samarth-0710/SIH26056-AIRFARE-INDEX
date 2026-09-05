from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration; production must set a PostgreSQL URL."""

    database_url: str = "sqlite:///./airfare_index.db"
    api_title: str = "SIH26056 Airfare Price Index API"
    environment: str = "development"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
