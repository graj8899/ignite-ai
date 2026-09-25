"""Application configuration, read from environment variables / .env.

Model names and other operational values are plain strings from the
environment — never hard-coded, never defaulted for secrets.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root .env (apps/api/app/config.py -> apps/api -> apps -> repo root).
_REPO_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_REPO_ROOT_ENV,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Secrets / required config — no defaults, so startup fails fast
    # if they are missing rather than silently running without them.
    openai_api_key: str
    auth_secret: str
    database_url: str

    # Model names — just strings from env, chosen per phase, never hard-coded.
    openai_model: str
    embedding_model: str

    # Non-secret operational config — safe to default for local dev.
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide Settings instance (built once, cached).

    Tests should not rely on this reading the real .env — override this
    dependency instead (see tests/conftest.py).
    """
    return Settings()
