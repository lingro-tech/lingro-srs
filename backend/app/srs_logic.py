#!/usr/bin/env python3
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv


# =============================
# 1. Подключение к БД
# =============================
load_dotenv()

PG_DB       = os.getenv("PG_DB")
PG_USER     = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_HOST     = os.getenv("PG_HOST", "localhost")
PG_PORT     = os.getenv("PG_PORT", "5432")

if not PG_DB or not PG_USER or not PG_PASSWORD:
    print("[ERROR] Missing DB params in .env", file=sys.stderr)
    sys.exit(1)

DSN = (
    f"dbname={PG_DB} user={PG_USER} password={PG_PASSWORD} "
    f"host={PG_HOST} port={PG_PORT}"
)


def get_conn():
    return psycopg2.connect(DSN, cursor_factory=DictCursor)


# =============================
# 2. SQL-запросы
# =============================

SQL_WORD_STATE_STATS = """
    SELECT COALESCE(state::text, 'NEW') AS st, COUNT(*) AS cnt
    FROM (
        SELECT w.id, uws.state
        FROM words w
        LEFT JOIN user_word_state uws
          ON uws.word_id = w.id AND uws.user_id = %(user_id)s
    ) t
    GROUP BY COALESCE(state::text, 'NEW')
    ORDER BY st;
"""

SQL_FIND_CANDIDATE_STRICT = """
WITH pw AS (
    SELECT
        pw.phrase_id,
        pw.word_id,
        COALESCE(uws.state::text, 'NEW') AS state
    FROM phrase_words pw
    LEFT JOIN user_word_state uws
      ON uws.word_id = pw.word_id
     AND uws.user_id = %(user_id)s
),
agg AS (
    SELECT
        pw.phrase_id,
        SUM(CASE WHEN state = 'NEW'   THEN 1 ELSE 0 END) AS n_new,
        SUM(CASE WHEN state = 'INTRO' THEN 1 ELSE 0 END) AS n_intro,
        SUM(CASE WHEN state = 'LEARN' THEN 1 ELSE 0 END) AS n_learn
    FROM pw
    GROUP BY pw.phrase_id
),
candidates AS (
    SELECT
        p.id,
        p.phrase,
        p.freq,
        a.n_new,
        a.n_intro,
        a.n_learn
    FROM agg a
    JOIN phrases p ON p.id = a.phrase_id
    LEFT JOIN user_phrase_history h
      ON h.user_id = %(user_id)s
     AND h.phrase_id = p.id
    WHERE a.n_new = 1
      AND h.phrase_id IS NULL
)
SELECT id, phrase, freq, n_new, n_intro, n_learn
FROM candidates
ORDER BY freq DESC
LIMIT 1;
"""

SQL_FIND_CANDIDATE_RELAXED = """
WITH pw AS (
    SELECT
        pw.phrase_id,
        pw.word_id,
        COALESCE(uws.state::text, 'NEW') AS state
    FROM phrase_words pw
    LEFT JOIN user_word_state uws
      ON uws.word_id = pw.word_id
     AND uws.user_id = %(user_id)s
),
agg AS (
    SELECT
        pw.phrase_id,
        SUM(CASE WHEN state = 'NEW'   THEN 1 ELSE 0 END) AS n_new,
        SUM(CASE WHEN state = 'INTRO' THEN 1 ELSE 0 END) AS n_intro,
        SUM(CASE WHEN state = 'LEARN' THEN 1 ELSE 0 END) AS n_learn
    FROM pw
    GROUP BY pw.phrase_id
)
SELECT
    p.id,
    p.phrase,
    p.freq,
    a.n_new,
    a.n_intro,
    a.n_learn
FROM agg a
JOIN phrases p ON p.id = a.phrase_id
WHERE a.n_new >= 1
ORDER BY p.freq DESC
LIMIT 1;
"""

SQL_FIND_TARGET_WORD = """
SELECT w.id AS word_id, w.word
FROM phrase_words pw
JOIN words w ON w.id = pw.word_id
LEFT JOIN user_word_state uws
  ON uws.word_id = pw.word_id
 AND uws.user_id = %(user_id)s
WHERE pw.phrase_id = %(phrase_id)s
  AND COALESCE(uws.state::text, 'NEW') = 'NEW'
ORDER BY pw.position
LIMIT 1;
"""


SQL_INSERT_HISTORY = """
INSERT INTO user_phrase_history (user_id, phrase_id, shown_at, result)
VALUES (%(user_id)s, %(phrase_id)s, %(shown_at)s, %(result)s);
"""

SQL_SELECT_WORD_STATES_FOR_PHRASE = """
SELECT
    w.id AS word_id,
    w.word,
    COALESCE(uws.state::text, 'NEW') AS state,
    uws.reps,
    uws.lapses,
    uws.next_due
FROM phrase_words pw
JOIN words w ON w.id = pw.word_id
LEFT JOIN user_word_state uws
  ON uws.word_id = pw.word_id
 AND uws.user_id = %(user_id)s
WHERE pw.phrase_id = %(phrase_id)s;
"""

SQL_UPSERT_WORD_STATE = """
INSERT INTO user_word_state (
    user_id, word_id, state, reps, lapses, last_result, last_seen, next_due
) VALUES (
    %(user_id)s, %(word_id)s, %(state)s, %(reps)s, %(lapses)s,
    %(last_result)s, %(last_seen)s, %(next_due)s
)
ON CONFLICT (user_id, word_id) DO UPDATE
SET state       = EXCLUDED.state,
    reps        = EXCLUDED.reps,
    lapses      = EXCLUDED.lapses,
    last_result = EXCLUDED.last_result,
    last_seen   = EXCLUDED.last_seen,
    next_due    = EXCLUDED.next_due;
"""


# =============================
# 3. Структуры данных
# =============================

@dataclass
class NextPhrase:
    phrase_id: int
    phrase: str
    freq: int
    n_new: int
    n_intro: int
    n_learn: int
    mode: str           # STRICT / RELAXED
    target_word_id: int | None
    target_word: str | None


# =============================
# 4. Логика выбора следующей фразы
# =============================

def get_next_phrase(user_id: int) -> NextPhrase | None:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # строгий режим
            cur.execute(SQL_FIND_CANDIDATE_STRICT, {"user_id": user_id})
            row = cur.fetchone()
            mode = "STRICT"

            if row is None:
                # ослабленный: допускаем уже виденные фразы
                cur.execute(SQL_FIND_CANDIDATE_RELAXED, {"user_id": user_id})
                row = cur.fetchone()
                mode = "RELAXED"

            if row is None:
                return None

            phrase_id = row["id"]
            phrase    = row["phrase"]
            freq      = row["freq"]
            n_new     = row["n_new"]
            n_intro   = row["n_intro"]
            n_learn   = row["n_learn"]

            # целевое слово (одно NEW-слово в фразе)
            cur.execute(
                SQL_FIND_TARGET_WORD,
                {"user_id": user_id, "phrase_id": phrase_id},
            )
            wrow = cur.fetchone()
            if wrow:
                target_word_id = wrow["word_id"]
                target_word    = wrow["word"]
            else:
                target_word_id = None
                target_word    = None

            return NextPhrase(
                phrase_id=phrase_id,
                phrase=phrase,
                freq=freq,
                n_new=n_new,
                n_intro=n_intro,
                n_learn=n_learn,
                mode=mode,
                target_word_id=target_word_id,
                target_word=target_word,
            )
    finally:
        conn.close()


# =============================
# 5. Обработка ответа SRS
#    answer_color: "red" | "yellow" | "green"
# =============================

def process_answer(user_id: int, phrase_id: int, answer_color: str) -> None:
    """
    Простая базовая логика SRS под 3 цвета:
      red    = "не знаю"         → откат, короткий интервал
      yellow = "знаю"            → нормальный рост интервала
      green  = "отлично знаю"    → быстрый рост интервала

    Для отладки: обновляем все СЛАБЫЕ слова фразы
    (NEW/INTRO/LEARN), KNOWN/MATURE сильно не трогаем.
    """
    if answer_color not in ("red", "yellow", "green"):
        raise ValueError("answer_color must be 'red', 'yellow' or 'green'")

    now = datetime.now(timezone.utc)

    # интервалы (можно будет подстроить)
    if answer_color == "red":
        delta = timedelta(days=0.5)   # через 12 часов
    elif answer_color == "yellow":
        delta = timedelta(days=2)     # через 2 дня
    else:  # green
        delta = timedelta(days=7)     # через неделю

    next_due = now + delta

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # 1) лог в user_phrase_history
            cur.execute(
                SQL_INSERT_HISTORY,
                {
                    "user_id": user_id,
                    "phrase_id": phrase_id,
                    "shown_at": now,
                    "result": answer_color,
                },
            )

            # 2) состояния слов во фразе
            cur.execute(
                SQL_SELECT_WORD_STATES_FOR_PHRASE,
                {"user_id": user_id, "phrase_id": phrase_id},
            )
            rows = cur.fetchall()

            for row in rows:
                word_id = row["word_id"]
                state   = row["state"] or "NEW"
                reps    = row["reps"] or 0
                lapses  = row["lapses"] or 0

                new_state = state

                if answer_color == "red":
                    # откат / закрепление
                    lapses += 1
                    if state in ("NEW", "INTRO"):
                        new_state = "INTRO"
                    else:
                        new_state = "LEARN"

                elif answer_color == "yellow":
                    # нормальное продвижение
                    reps += 1
                    if state in ("NEW", "INTRO"):
                        new_state = "LEARN"
                    elif state == "LEARN":
                        new_state = "LEARN"
                    elif state == "KNOWN":
                        new_state = "KNOWN"

                else:  # green
                    reps += 1
                    if state in ("NEW", "INTRO"):
                        new_state = "LEARN"
                    elif state == "LEARN":
                        new_state = "KNOWN"
                    elif state == "KNOWN":
                        new_state = "KNOWN"

                cur.execute(
                    SQL_UPSERT_WORD_STATE,
                    {
                        "user_id": user_id,
                        "word_id": word_id,
                        "state": new_state,
                        "reps": reps,
                        "lapses": lapses,
                        "last_result": answer_color,
                        "last_seen": now,
                        "next_due": next_due,
                    },
                )

        conn.commit()
    finally:
        conn.close()
