from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings loaded exclusively from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=(str(ROOT_DIR / ".env"), str(BACKEND_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "PulseGrid"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = f"sqlite:///{(BACKEND_DIR / 'pulsegrid.db').as_posix()}"
    SECRET_KEY: str = Field(..., min_length=16)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    DEMO_MODE: bool = False
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:4173"

    # University policy defaults
    CURRENT_WEEK: int = 9
    TOTAL_WEEKS: int = 14
    ATTENDANCE_THRESHOLD: float = 0.75
    INTERNAL_THRESHOLD: float = 0.40
    THEORY_SESSIONS_PER_WEEK: int = 3
    LAB_SESSIONS_PER_WEEK: int = 2
    LOG_LEVEL: str = "INFO"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
