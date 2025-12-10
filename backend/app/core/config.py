from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Корень репозитория (…/lingro-srs)
ENV_PATH = Path(__file__).resolve().parents[2]
ENV_FILE = ENV_PATH / ".env"

# Загружаем .env из корня репозитория
load_dotenv(dotenv_path=ENV_FILE, override=True)


class Settings(BaseSettings):
    # ОБЯЗАТЕЛЬНЫЕ значения — должны быть в .env
    DATABASE_URL: str
    TELEGRAM_BOT_TOKEN: str
    JWT_SECRET_KEY: str

    # Второстепенные дефолты
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 дней

    DEV_LOGIN_SECRET: str | None = None

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> "Settings":
    return Settings()


settings = get_settings()
