from datetime import datetime, timedelta, timezone

from jose import jwt

from .config import settings


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    subject — строковый идентификатор (обычно user.id),
    который кладём в claim "sub".
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode = {
        "sub": subject,
        "exp": expire,
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt
