from functools import lru_cache
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(BASE_DIR / ".env"), str(BASE_DIR.parent / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "dev"
    APP_NAME: str = "JanSamadhan AI - E-Governance Grievance Redressal"
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "dev-super-secret-change-in-production-32chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    DATABASE_URL: str = f"sqlite:///{(BASE_DIR / 'grievance_dev.db').as_posix()}"
    JOB_RUNNER: str = "apscheduler"
    REDIS_URL: str = "redis://localhost:6379/0"

    AI_PROVIDER: str = "fallback"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    MAX_UPLOAD_SIZE_MB: int = 5
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    DEMO_MODE: bool = True

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
