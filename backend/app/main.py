from fastapi import FastAPI

from .api.v1.routes_auth import router as auth_router

app = FastAPI(
    title="Lingro SRS API",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {"status": "ok"}


# Подключаем namespace /api/v1/auth
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])


# --------- временные SRS-заглушки, оставим как есть ---------

from pydantic import BaseModel


class SRSCard(BaseModel):
    id: int
    text: str
    translation: str | None = None
    language: str = "es"


class ReviewRequest(BaseModel):
    card_id: int
    grade: int  # 1..4


class ReviewResponse(BaseModel):
    next_card: SRSCard | None = None


@app.get("/api/v1/srs/next", response_model=SRSCard)
async def get_next_card():
    return SRSCard(
        id=1,
        text="¿Dónde está el baño?",
        translation="Где находится туалет?",
        language="es",
    )


@app.post("/api/v1/srs/review", response_model=ReviewResponse)
async def review(payload: ReviewRequest):
    next_card = SRSCard(
        id=2,
        text="Muchas gracias.",
        translation="Большое спасибо.",
        language="es",
    )
    return ReviewResponse(next_card=next_card)
