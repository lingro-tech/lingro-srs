from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...schemas.auth import TelegramAuthPayload, TokenResponse
from ...services.telegram_auth import verify_telegram_auth
from ...core.security import create_access_token
from ...db.session import get_session
from ...models.user import User

router = APIRouter()


@router.post("/telegram", response_model=TokenResponse)
async def telegram_login(payload: TelegramAuthPayload, db: Session = Depends(get_session)):
    """
    Эндпоинт для авторизации через Telegram Login Widget.
    На вход — данные из JS, на выход — JWT-токен.
    """
    data = payload.model_dump()

    if not verify_telegram_auth(data):
        raise HTTPException(status_code=400, detail="Invalid Telegram auth data")

    user = db.query(User).filter(User.telegram_id == payload.id).first()

    if user is None:
        user = User(telegram_id=payload.id)

    user.username = payload.username
    user.first_name = payload.first_name
    user.last_name = payload.last_name
    user.photo_url = payload.photo_url

    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(subject=str(user.id))

    return TokenResponse(access_token=access_token)
