from fastapi import APIRouter, Depends

from ...core.security import get_current_user
from ...models.user import User
from ...schemas.user import UserRead

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
