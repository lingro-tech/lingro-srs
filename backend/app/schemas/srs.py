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
