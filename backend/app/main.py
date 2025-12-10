from fastapi import FastAPI

from .api.v1.routes_auth import router as auth_router
from .api.v1.routes_srs import router as srs_router
from .api.v1.routes_users import router as users_router
from .db.session import init_models

app = FastAPI(
    title="Lingro SRS API",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
async def on_startup():
    # Создаём таблицы, если их нет. Пока простая синхронная инициализация для SQLite.
    init_models()


# Подключаем namespace /api/v1/auth
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

# SRS эндпоинты
app.include_router(srs_router, prefix="/api/v1/srs", tags=["srs"])

# Пользовательские эндпоинты
app.include_router(users_router, prefix="/api/v1", tags=["users"])
