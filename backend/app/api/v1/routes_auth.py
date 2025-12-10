from fastapi import APIRouter, HTTPException

from ...schemas.auth import TelegramAuthPayload, TokenResponse
from ...services.telegram_auth import verify_telegram_auth
from ...core.security import create_access_token

router = APIRouter()


@router.post("/telegram", response_model=TokenResponse)
async def telegram_login(payload: TelegramAuthPayload):
    """
    Эндпоинт для авторизации через Telegram Login Widget.
    На вход — данные из JS, на выход — JWT-токен.
    """
    data = payload.dict()

    if not verify_telegram_auth(data):
        raise HTTPException(status_code=400, detail="Invalid Telegram auth data")

    # В реальном варианте здесь:
    #   1) ищем/создаём пользователя в БД
    #   2) берем его внутренний user_id
    #   3) шьём его в токен
    # Пока используем просто Telegram ID как subject.
    telegram_id = payload.id
    access_token = create_access_token(subject=str(telegram_id))

    return TokenResponse(access_token=access_token)
