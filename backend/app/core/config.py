from functools import lru_cache
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_DB_PATH = (_REPO_ROOT / "airfare_index.db").resolve()


class Settings(BaseSettings):
    """Runtime configuration; production must set a PostgreSQL URL."""

    database_url: str = f"sqlite:///{_DEFAULT_DB_PATH}"
    api_title: str = "SIH26056 Airfare Price Index API"
    environment: str = "development"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url", mode="after")
    @classmethod
    def resolve_sqlite_path(cls, v: str) -> str:
        if v.startswith("sqlite:///./"):
            rel = v[len("sqlite:///./") :]
            return f"sqlite:///{(_REPO_ROOT / rel).resolve()}"
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
