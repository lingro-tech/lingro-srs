from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes_auth import router as auth_router
from .api.routes_srs import router as srs_router
from .api.routes_users import router as users_router

app = FastAPI(
    title="Lingro SRS API",
    version="0.1.0",
)

# Разрешённые источники (откуда приходит фронт)
origins = [
    "http://192.168.1.66:3000",  # твой Edge/Chrome
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(srs_router, prefix="/api/v1/srs", tags=["srs"])
app.include_router(users_router, prefix="/api/v1", tags=["users"])
