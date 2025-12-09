#!/usr/bin/env python3
"""
Перевод испанских фраз из БД на английский с помощью локальной модели
NLLB-200 distilled 600M.

Таблица (существующая):

    CREATE TABLE public.phrases (
        id            integer PRIMARY KEY,
        phrase        text    NOT NULL,  -- испанская фраза
        freq          integer NOT NULL,
        cluster_size  integer NOT NULL,
        length        smallint NOT NULL,
        tts_ok        boolean NOT NULL DEFAULT false,
        tts_attempts  integer NOT NULL DEFAULT 0,
        tts_error     text
    );

Дополнительно под перевод:

    ALTER TABLE public.phrases
        ADD COLUMN phrase_en text;

Скрипт выбирает записи, где phrase_en IS NULL, переводит phrase -> phrase_en
и записывает результат обратно.

Подключение к БД берётся из .env:

    PG_DB
    PG_USER
    PG_PASSWORD
    PG_HOST
    PG_PORT
"""

import argparse
import os
import sys
from typing import List, Tuple

import psycopg2
import psycopg2.extras
from tqdm import tqdm

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from dotenv import load_dotenv


# ============================================================
#  МОДЕЛЬ NLLB-200 600M
# ============================================================

MODEL_NAME = "facebook/nllb-200-distilled-600M"

# Языковые коды NLLB
SRC_LANG = "spa_Latn"  # испанский
TGT_LANG = "eng_Latn"  # английский


def load_model(model_name: str = MODEL_NAME,
               tgt_lang: str = TGT_LANG):
    """
    Загружаем токенайзер и модель NLLB-200 600M на GPU (если есть).
    """
    print(f"Loading tokenizer: {model_name}", file=sys.stderr)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.src_lang = SRC_LANG  # задаём язык источника

    print(f"Loading model: {model_name}", file=sys.stderr)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # dtype вместо устаревшего torch_dtype
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_name,
        dtype=torch.float16 if device == "cuda" else torch.float32,
    ).to(device)

    forced_bos_token_id = tokenizer.convert_tokens_to_ids(tgt_lang)

    return tokenizer, model, device, forced_bos_token_id


def translate_batch(
    sentences: List[str],
    tokenizer,
    model,
    device: str,
    forced_bos_token_id: int,
    max_length: int = 128,
) -> List[str]:
    """
    Перевод списка предложений.
    """
    if not sentences:
        return []

    inputs = tokenizer(
        sentences,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_length,
    ).to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            max_length=max_length,
        )

    decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    return [s.strip() for s in decoded]


# ============================================================
#  РАБОТА С БД
# ============================================================

def build_dsn_from_env() -> str:
    """
    Собираем DSN для psycopg2 из переменных окружения.

    Ожидаются переменные:
        PG_DB, PG_USER, PG_PASSWORD, PG_HOST, PG_PORT
    """
    host = os.getenv("PG_HOST", "localhost")
    port = os.getenv("PG_PORT", "5432")
    dbname = os.getenv("PG_DB")
    user = os.getenv("PG_USER")
    password = os.getenv("PG_PASSWORD")

    missing = [name for name, val in [
        ("PG_DB", dbname),
        ("PG_USER", user),
        ("PG_PASSWORD", password),
    ] if not val]

    if missing:
        raise RuntimeError(
            f"Отсутствуют необходимые переменные окружения для БД: {', '.join(missing)}"
        )

    dsn = (
        f"dbname={dbname} user={user} password={password} "
        f"host={host} port={port}"
    )
    return dsn


def fetch_batch(
    conn,
    table: str,
    src_col: str,
    tgt_col: str,
    batch_size: int,
) -> List[Tuple[int, str]]:
    """
    Забираем batch из БД: id и исходный текст.
    Берём только строки, где tgt_col IS NULL.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        query = f"""
            SELECT id, {src_col}
            FROM {table}
            WHERE {tgt_col} IS NULL
              AND {src_col} IS NOT NULL
              AND length({src_col}) > 0
            ORDER BY id
            LIMIT %s
        """
        cur.execute(query, (batch_size,))
        rows = cur.fetchall()

    return [(r["id"], r[src_col]) for r in rows]


def update_translations(
    conn,
    table: str,
    tgt_col: str,
    rows: List[Tuple[int, str]],
):
    """
    Обновляем переводы в БД.
    rows: список (id, translated_text).
    """
    if not rows:
        return

    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(
            cur,
            f"UPDATE {table} SET {tgt_col} = %s WHERE id = %s",
            [(text, _id) for _id, text in rows],
            page_size=1000,
        )
    conn.commit()


# ============================================================
#  MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Перевод испанских фраз из public.phrases на английский "
                    "с помощью NLLB-200 600M (DSN из .env)."
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Путь к .env-файлу с параметрами подключения к БД (по умолчанию: .env).",
    )
    parser.add_argument(
        "--table",
        default="public.phrases",
        help="Имя таблицы с фразами (по умолчанию: public.phrases).",
    )
    parser.add_argument(
        "--src-col",
        default="phrase",
        help="Имя столбца с исходным испанским текстом (по умолчанию: phrase).",
    )
    parser.add_argument(
        "--tgt-col",
        default="phrase_en",
        help="Имя столбца для записи перевода (по умолчанию: phrase_en).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=128,
        help="Размер batch для перевода (по умолчанию: 128).",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=0,
        help=(
            "Максимальное количество строк для обработки. "
            "0 = без ограничения (по умолчанию: 0)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Не записывать переводы в БД, только считать и тестировать.",
    )

    args = parser.parse_args()

    # Загружаем .env
    if args.env_file:
        if os.path.exists(args.env_file):
            load_dotenv(args.env_file)
            print(f"Loaded .env from {args.env_file}", file=sys.stderr)
        else:
            print(
                f"Warning: .env file '{args.env_file}' not found, "
                f"используются переменные окружения процесса.",
                file=sys.stderr,
            )

    # Собираем DSN
    dsn = build_dsn_from_env()

    print(f"Connecting to DB with DSN: {dsn}", file=sys.stderr)
    conn = psycopg2.connect(dsn)

    # Грузим модель
    tokenizer, model, device, forced_bos_token_id = load_model()

    total_processed = 0

    try:
        with tqdm(total=args.max_rows if args.max_rows > 0 else None,
                  unit="rows") as pbar:
            while True:
                if args.max_rows > 0:
                    remaining = args.max_rows - total_processed
                    if remaining <= 0:
                        break
                    batch_size = min(args.batch_size, remaining)
                else:
                    batch_size = args.batch_size

                batch = fetch_batch(
                    conn,
                    table=args.table,
                    src_col=args.src_col,
                    tgt_col=args.tgt_col,
                    batch_size=batch_size,
                )

                if not batch:
                    break  # всё перевели

                ids, src_texts = zip(*batch)

                translations = translate_batch(
                    list(src_texts),
                    tokenizer,
                    model,
                    device,
                    forced_bos_token_id,
                )

                id_text_pairs = list(zip(ids, translations))

                total_processed += len(id_text_pairs)

                if not args.dry_run:
                    update_translations(
                        conn,
                        table=args.table,
                        tgt_col=args.tgt_col,
                        rows=id_text_pairs,
                    )

                pbar.update(len(id_text_pairs))

                if args.max_rows > 0 and total_processed >= args.max_rows:
                    break

    finally:
        conn.close()

    print(f"Done. processed={total_processed}", file=sys.stderr)


if __name__ == "__main__":
    main()
