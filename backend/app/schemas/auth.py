from pydantic import BaseModel


class TelegramAuthPayload(BaseModel):
    """
    Поля Telegram Login Widget.
    Допускаем лишние поля, чтобы не падать на неожиданных.
    """

    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str

    class Config:
        extra = "allow"  # игнорировать лишние поля


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
