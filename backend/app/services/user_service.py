from sqlalchemy.orm import Session

from ..models.user import User
from ..schemas.auth import TelegramAuthPayload


def get_or_create_user_by_telegram_id(db: Session, payload: TelegramAuthPayload) -> User:
    user = db.query(User).filter(User.telegram_id == payload.id).first()

    if user is None:
        user = User(telegram_id=payload.id)
        db.add(user)

    user.username = payload.username
    user.first_name = payload.first_name
    user.last_name = payload.last_name
    user.photo_url = payload.photo_url

    db.commit()
    db.refresh(user)

    return user
