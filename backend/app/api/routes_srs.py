from fastapi import APIRouter

from ..schemas.srs import ReviewRequest, ReviewResponse, SRSCard

router = APIRouter()


@router.get("/next", response_model=SRSCard)
async def get_next_card():
    return SRSCard(
        id=1,
        text="¿Dónde está el baño?",
        translation="Где находится туалет?",
        language="es",
    )


@router.post("/review", response_model=ReviewResponse)
async def review(payload: ReviewRequest):
    next_card = SRSCard(
        id=2,
        text="Muchas gracias.",
        translation="Большое спасибо.",
        language="es",
    )
    return ReviewResponse(next_card=next_card)
