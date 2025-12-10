from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .deps import get_db
from ..core.config import settings
from ..core.security import create_access_token
from ..schemas.auth import TelegramAuthPayload, TokenResponse
from ..services.telegram_auth import verify_telegram_auth
from ..services.user_service import get_or_create_user_by_telegram_id

router = APIRouter()


@router.post("/telegram", response_model=TokenResponse)
async def telegram_login(
    payload: TelegramAuthPayload,
    db: Session = Depends(get_db),
):
    ...
    # как уже сделали раньше
    ...


# ===== DEV-логин (для локальной отладки) =====

@router.post("/dev-login", response_model=TokenResponse)
async def dev_login(
    telegram_id: int,
    username: str | None = None,
    secret: str | None = None,
    db: Session = Depends(get_db),
):
    """
    DEV-эндпоинт для локальной отладки без Telegram.

    ВЫЗЫВАТЬ ТОЛЬКО ЛОКАЛЬНО.

    Пример:
        POST /api/v1/auth/dev-login?telegram_id=123&username=test&secret=local_dev_only
    """

    if settings.DEV_LOGIN_SECRET is None or secret != settings.DEV_LOGIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    # минимальный fake-payload для reuse логики
    payload = TelegramAuthPayload(
        id=telegram_id,
        username=username,
        first_name=None,
        last_name=None,
        photo_url=None,
        auth_date=0,
        hash="dev",
    )

    user = get_or_create_user_by_telegram_id(db, payload)
    access_token = create_access_token(subject=str(user.id))

    return TokenResponse(access_token=access_token)
