from sqlalchemy.orm import Session

from ..models.user import User
from ..schemas.auth import TelegramAuthPayload
from ..schemas.user import UserCreate


def get_user_by_telegram_id(db: Session, telegram_id: int) -> User | None:
    return db.query(User).filter(User.telegram_id == telegram_id).one_or_none()


def create_user_from_telegram(db: Session, payload: TelegramAuthPayload) -> User:
    data = UserCreate(
        telegram_id=payload.id,
        username=payload.username,
        first_name=payload.first_name,
        last_name=payload.last_name,
        photo_url=payload.photo_url,
    )
    user = User(
        telegram_id=data.telegram_id,
        username=data.username,
        first_name=data.first_name,
        last_name=data.last_name,
        photo_url=data.photo_url,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_user_by_telegram_id(db: Session, payload: TelegramAuthPayload) -> User:
    user = get_user_by_telegram_id(db, payload.id)
    if user is not None:
        return user
    return create_user_from_telegram(db, payload)
