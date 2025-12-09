#!/usr/bin/env python3
"""
Генерация 512x512 картинок для фраз из таблицы public.phrases
с возможностью продолжения после остановки и использованием
локально сохранённой модели Stable Diffusion.
"""

import argparse
import os
from pathlib import Path

import torch
from diffusers import StableDiffusionPipeline
from diffusers.utils import is_peft_available
from dotenv import load_dotenv
from tqdm import tqdm
import psycopg2


# -------------------------------
# Настройки модели
# -------------------------------
REMOTE_MODEL_ID = "runwayml/stable-diffusion-v1-5"
DEFAULT_LOCAL_MODEL_DIR = Path("/home/ol/nvme512/models/sd15")

STYLE_PROMPT_PREFIX = (
    "children's book illustration, simple flat style, soft minimal shapes, "
    "white background, isolated object, no border, no shadow, no background, "
    "high quality"
)

NEGATIVE_PROMPT = (
    "background, clutter, text, watermark, logo, noise, hyperrealistic, 3d, "
    "photo, photographic, shadows, dark background, extra limbs, mutated, distorted"
)


# -------------------------------
# DB connection
# -------------------------------
def load_db_connection():
    load_dotenv()

    conn = psycopg2.connect(
        dbname=os.environ.get("PG_DB", "postgres"),
        user=os.environ.get("PG_USER", "postgres"),
        password=os.environ.get("PG_PASSWORD", ""),
        host=os.environ.get("PG_HOST", "localhost"),
        port=os.environ.get("PG_PORT", "5432"),
    )
    conn.autocommit = True
    return conn


# -------------------------------
# State file helpers
# -------------------------------
def load_last_id(state_path: Path):
    if not state_path.exists():
        return None
    try:
        return int(state_path.read_text().strip())
    except Exception:
        return None


def save_last_id(state_path: Path, phrase_id: int):
    state_path.write_text(str(phrase_id))


# -------------------------------
# Local model handling
# -------------------------------
def ensure_local_model(model_dir: Path, device: str):
    model_dir = model_dir.expanduser().absolute()
    model_dir.mkdir(parents=True, exist_ok=True)

    model_index = model_dir / "model_index.json"
    if model_index.exists():
        print(f"[model] Using existing local SD model: {model_dir}")
        return model_dir

    print(f"[model] Local model missing → downloading from HF: {REMOTE_MODEL_ID}")

    pipe = StableDiffusionPipeline.from_pretrained(
        REMOTE_MODEL_ID,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    )
    pipe.save_pretrained(model_dir)
    print(f"[model] Saved model to: {model_dir}")

    del pipe
    torch.cuda.empty_cache()
    return model_dir


# -------------------------------
# SQL helpers
# -------------------------------
def get_total_rows(conn, last_id, limit, offset):
    with conn.cursor() as cur:
        if last_id is not None:
            if limit is None:
                cur.execute(
                    "SELECT COUNT(*) FROM public.phrases WHERE id > %s",
                    (last_id,),
                )
            else:
                cur.execute(
                    "SELECT COUNT(*) FROM ("
                    "  SELECT id FROM public.phrases WHERE id > %s "
                    "  ORDER BY id LIMIT %s"
                    ") t",
                    (last_id, limit),
                )
        else:
            if limit is None:
                cur.execute(
                    "SELECT COUNT(*) FROM public.phrases OFFSET %s",
                    (offset,),
                )
            else:
                cur.execute(
                    "SELECT COUNT(*) FROM ("
                    "  SELECT id FROM public.phrases "
                    "  ORDER BY id LIMIT %s OFFSET %s"
                    ") t",
                    (limit, offset),
                )
        return cur.fetchone()[0]


def iter_phrases(conn, last_id, limit, offset=0):
    """
    Итератор по (id, phrase) без именованного курсора.
    """
    with conn.cursor() as cur:
        if last_id is not None:
            if limit is None:
                cur.execute(
                    "SELECT id, phrase FROM public.phrases "
                    "WHERE id > %s ORDER BY id",
                    (last_id,),
                )
            else:
                cur.execute(
                    "SELECT id, phrase FROM public.phrases "
                    "WHERE id > %s ORDER BY id LIMIT %s",
                    (last_id, limit),
                )
        else:
            if limit is None:
                cur.execute(
                    "SELECT id, phrase FROM public.phrases "
                    "ORDER BY id OFFSET %s",
                    (offset,),
                )
            else:
                cur.execute(
                    "SELECT id, phrase FROM public.phrases "
                    "ORDER BY id LIMIT %s OFFSET %s",
                    (limit, offset),
                )

        while True:
            rows = cur.fetchmany(1000)
            if not rows:
                break
            for r in rows:
                yield r[0], r[1]


# -------------------------------
# Prompt builder
# -------------------------------
def build_prompt(phrase: str) -> str:
    return f'{STYLE_PROMPT_PREFIX}, for phrase: "{phrase.strip()}"'


# -------------------------------
# Main script
# -------------------------------
def main():
    parser = argparse.ArgumentParser("Stable Diffusion card generator")
    parser.add_argument("--out-dir", type=Path, default=Path("data"))
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_LOCAL_MODEL_DIR)
    parser.add_argument("--lora", type=Path, required=True)
    parser.add_argument("--num-steps", type=int, default=20)
    parser.add_argument("--guidance-scale", type=float, default=7.5)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--state-file", type=Path, default=None)
    parser.add_argument("--ignore-state", action="store_true")

    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    state_path = args.state_file or (args.out_dir / "cards_state.txt")

    device = "cuda" if torch.cuda.is_available() else "cpu"

    # DB
    conn = load_db_connection()

    # Local model
    local_model_dir = ensure_local_model(args.model_dir, device=device)

    # Load pipeline from local model
    pipe = StableDiffusionPipeline.from_pretrained(
        local_model_dir,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        safety_checker=None,
    ).to(device)

    # memory optimizations
    pipe.enable_attention_slicing()
    if hasattr(pipe, "vae") and hasattr(pipe.vae, "enable_slicing"):
        pipe.vae.enable_slicing()

    # LoRA loading
    if not is_peft_available():
        raise RuntimeError("PEFT package required: pip install peft")

    lora_path: Path = args.lora

    if lora_path.suffix.lower() in {".safetensors", ".bin"}:
        if not lora_path.is_file():
            raise FileNotFoundError(f"LoRA file not found: {lora_path}")
        pipe.load_lora_weights(
            str(lora_path.parent),   # директория
            weight_name=lora_path.name,
        )
    else:
        if not lora_path.is_dir():
            raise FileNotFoundError(f"LoRA directory not found: {lora_path}")
        pipe.load_lora_weights(str(lora_path))

    if hasattr(pipe, "fuse_lora"):
        pipe.fuse_lora()

    # State
    last_id = None if args.ignore_state else load_last_id(state_path)
    if last_id:
        print(f"[state] Resuming after id={last_id}")
    else:
        print("[state] Starting fresh (limit/offset active)")

    # RNG
    generator = torch.Generator(device=device).manual_seed(args.seed) if args.seed else None

    total = get_total_rows(conn, last_id, args.limit, args.offset)
    if total == 0:
        print("Nothing to process.")
        return

    phrase_iter = iter_phrases(conn, last_id, args.limit, args.offset)

    current_last_id = last_id

    for pid, phrase in tqdm(phrase_iter, total=total, desc="Generating"):
        out_path = args.out_dir / f"{pid}.png"
        if out_path.exists():
            current_last_id = pid
            save_last_id(state_path, pid)
            continue

        prompt = build_prompt(phrase)

        img = pipe(
            prompt=prompt,
            negative_prompt=NEGATIVE_PROMPT,
            num_inference_steps=args.num_steps,
            guidance_scale=args.guidance_scale,
            height=512,
            width=512,
            generator=generator,
        ).images[0]

        img.save(out_path)

        current_last_id = pid
        save_last_id(state_path, pid)

    print(f"[state] Finished up to id={current_last_id}")
    conn.close()


if __name__ == "__main__":
    main()
