from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...schemas.auth import TelegramAuthPayload, TokenResponse
from ...services.telegram_auth import verify_telegram_auth
from ...core.security import create_access_token
from ...db.session import get_db
from ...services.user_service import get_or_create_user_by_telegram_id

router = APIRouter()


@router.post("/telegram", response_model=TokenResponse)
async def telegram_login(payload: TelegramAuthPayload, db: Session = Depends(get_db)):
    """
    Эндпоинт для авторизации через Telegram Login Widget.
    На вход — данные из JS, на выход — JWT-токен.
    """
    data = payload.model_dump()

    if not verify_telegram_auth(data):
        raise HTTPException(status_code=400, detail="Invalid Telegram auth data")

    user = get_or_create_user_by_telegram_id(db, payload)

    access_token = create_access_token({"sub": str(user.id)})

    return TokenResponse(access_token=access_token)
