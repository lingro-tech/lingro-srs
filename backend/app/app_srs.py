#!/usr/bin/env python3
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from srs_logic import get_next_phrase, process_answer


app = FastAPI(title="SRS Debug API")


# ---------- API-модели ----------

class AnswerRequest(BaseModel):
    user_id: int = 1
    phrase_id: int
    answer_color: str  # "red" | "yellow" | "green"


# ---------- API-эндпоинты ----------

@app.get("/api/next_phrase")
async def api_next_phrase(user_id: int = 1):
    np = get_next_phrase(user_id)
    if np is None:
        return {"status": "NO_PHRASE"}

    return {
        "status": "OK",
        "user_id": user_id,
        "phrase_id": np.phrase_id,
        "phrase": np.phrase,
        "freq": np.freq,
        "n_new": np.n_new,
        "n_intro": np.n_intro,
        "n_learn": np.n_learn,
        "mode": np.mode,
        "target_word_id": np.target_word_id,
        "target_word": np.target_word,
    }


@app.post("/api/answer")
async def api_answer(req: AnswerRequest):
    process_answer(
        user_id=req.user_id,
        phrase_id=req.phrase_id,
        answer_color=req.answer_color,
    )
    return {"status": "OK"}


# ---------- Статика и корневая страница ----------

# /static/* → файлы из каталога static
app.mount("/static", StaticFiles(directory="static"), name="static")


# / → отдаём index.html
@app.get("/")
async def index():
    return FileResponse("static/index.html")
