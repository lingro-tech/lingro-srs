from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    id: int
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    photo_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
