from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Analisis de Compras API"
    app_env: str = "development"
    log_level: str = "INFO"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"

    tavily_api_key: str = ""

    database_url: str = "sqlite:///./backend/data/analisis_compras.db"

    cors_origins: str = "http://localhost:3000"

    @field_validator("database_url")
    @classmethod
    def resolve_sqlite_path(cls, value: str) -> str:
        prefix = "sqlite:///"
        if value.startswith(prefix):
            raw = value[len(prefix):]
            if raw.startswith("./"):
                path = (PROJECT_ROOT / raw[2:]).resolve()
                return f"{prefix}{path.as_posix()}"
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
