from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Общие
    ENV: str = "dev"

    # Пока заглушка, позже заменим на PostgreSQL
    DATABASE_URL: str = "sqlite:///./lingro.db"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = "CHANGE_ME"

    # JWT
    JWT_SECRET_KEY: str = "CHANGE_ME_TOO"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 дней

    # Настройки загрузки из .env для Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> "Settings":
    return Settings()


settings = get_settings()

