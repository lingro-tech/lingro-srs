from fastapi import APIRouter
import random

from ..schemas.srs import ReviewRequest, ReviewResponse, SRSCard

router = APIRouter()

# Наши тестовые SRS-карточки
CARDS = [
    SRSCard(
        id=1,
        text="¿Dónde está el baño?",
        translation="Где находится туалет?",
        language="es",
    ),
    SRSCard(
        id=2,
        text="Muchas gracias.",
        translation="Большое спасибо.",
        language="es",
    ),
    SRSCard(
        id=3,
        text="¿Cuántos años tienes?",
        translation="Сколько тебе лет?",
        language="es",
    ),
    SRSCard(
        id=4,
        text="Buenas noches.",
        translation="Доброй ночи.",
        language="es",
    ),
]


@router.get("/next", response_model=SRSCard)
async def get_next_card():
    return random.choice(CARDS)


@router.post("/review", response_model=ReviewResponse)
async def review(payload: ReviewRequest):
    # Здесь пока не используем payload.grade, просто отдаём следующую случайную
    next_card = random.choice(CARDS)
    return ReviewResponse(next_card=next_card)
