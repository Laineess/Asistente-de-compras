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
    gemini_timeout_seconds: float = 30.0
    gemini_retries: int = 0

    tavily_api_key: str = ""

    database_url: str = "sqlite:///./backend/data/analisis_compras.db"

    cors_origins: str = "http://localhost:3000"

    telegram_bot_token: str = ""
    telegram_allowed_user_ids: str = ""
    bot_default_mode: str = "fast"
    bot_session_ttl_hours: int = 24
    bot_rate_limit_per_hour: int = 10
    bot_max_audio_seconds: int = 120
    bot_voice_reply_mode: str = "auto"
    telegram_tts_voice: str = "es-MX-JorgeNeural"
    telegram_stt_model: str = "small"
    telegram_stt_device: str = "cpu"
    telegram_stt_compute_type: str = "int8"

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

    @property
    def telegram_allowed_user_ids_set(self) -> set[int]:
        values: set[int] = set()
        for raw in self.telegram_allowed_user_ids.split(","):
            raw = raw.strip()
            if raw.isdigit():
                values.add(int(raw))
        return values

    @property
    def bot_session_db_path(self) -> Path:
        return PROJECT_ROOT / "backend/data/bot_sessions.db"


settings = Settings()
