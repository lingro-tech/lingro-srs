#!/usr/bin/env python
import json
import os
import time
import re
import requests
from pathlib import Path
from tqdm import tqdm

# ==========================
#   ПУТИ
# ==========================

# входной корпус (по строке на фразу)
SOURCE_CORPUS = Path("corpus/es.filtered.txt")

# чистый корпус для обучения (по строке, уже очищенный LLM)
OUTPUT_TEXT = Path("corpus/es.llm_clean.txt")

# jsonl с метаданными (для БД)
OUTPUT_META = Path("corpus/es_llm_filtered.jsonl")

# чекпоинт — номер строки во входном SOURCE_CORPUS
CHECKPOINT = Path("corpus/es.llm_filter_checkpoint.json")

# ==========================
#   ПАРАМЕТРЫ
# ==========================

# сколько фраз отправляем в LLM за один запрос
BATCH_SIZE = 16

# грубый лимит по суммарной длине фраз в батче (символы)
MAX_CHARS_PER_BATCH = 1200

# максимальная длина одной строки, которую отправляем в LLM
MAX_CHARS_PER_LINE = 120

# Настройки LLM (OpenAI-совместимый API)
BASE_URL = "http://localhost:8000/v1"
API_KEY = "dummy-key"

# ДОЛЖЕН СОВПАДАТЬ со строкой --model при запуске vLLM
# у вас: vllm serve models/qwen25-15b ...
MODEL = "models/qwen25-15b"

SESSION = requests.Session()

# ==========================
#   ЧЕКПОИНТ
# ==========================


def load_checkpoint() -> int:
    """
    Вернуть номер последней обработанной строки входного файла.
    -1, если чекпоинта нет или он битый.
    """
    if CHECKPOINT.exists():
        try:
            data = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
            return int(data.get("last_line", -1))
        except Exception:
            return -1
    return -1


def save_checkpoint(last_line: int) -> None:
    """
    Атомарно сохранить номер последней полностью обработанной строки.
    """
    tmp = CHECKPOINT.with_suffix(".tmp")
    tmp.write_text(json.dumps({"last_line": last_line}), encoding="utf-8")
    tmp.replace(CHECKPOINT)


# ==========================
#   LLM
# ==========================

SYSTEM_PROMPT = """
Eres lingüista nativo de español y especialista en enseñanza de español.

Tarea:
- Recibes varias frases originales en español.
- Para cada frase decides si sirve para tarjetas de estudio de español para extranjeros.
- Si sirve (keep = true), devuelves también una versión limpia.

BUENA FRASE (keep = true):
- 2–7 palabras.
- Oración o réplica casi completa.
- Útil en situaciones cotidianas.
- Español moderno y natural.

MALA FRASE (keep = false):
- Fragmento sin sentido claro.
- Demasiados nombres propios, lugares, títulos, marcas.
- Fechas, horas, números concretos.
- Ruido de subtítulos (aplausos, risas, indicaciones técnicas).
- No está en español o es muy rara.

Si keep = true, campo "clean":
- sólo palabras en español en minúsculas,
- sin signos de puntuación, números ni símbolos,
- sin nombres propios evidentes,
- palabras separadas por un solo espacio.

ENTRADA:
JSON con clave "phrases", lista de objetos: {"id": 0, "text": "frase original"}

SALIDA:
Sólo JSON con lista de objetos:
[
  {"id": 0, "keep": true,  "clean": "frase limpia en minusculas"},
  {"id": 1, "keep": false, "clean": ""}
]
""".strip()


# ========= безопасный JSON-парсер =========
def safe_parse_json(s: str):
    s = s.strip()

    # отрезать всё до первой '[' (если модель что-то дописала до массива)
    i = s.find("[")
    if i > 0:
        s = s[i:]

    # попытка 1 — как есть
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass

    # попытка 2: обрезать после последней '}'
    last_brace = s.rfind("}")
    if last_brace != -1:
        s2 = s[: last_brace + 1]
        if not s2.strip().endswith("]"):
            s2 += "]"
        try:
            return json.loads(s2)
        except json.JSONDecodeError:
            pass

    # попытка 3: собрать все полные объекты вида {...}
    objs = re.findall(r"\{[^{}]*\}", s, flags=re.DOTALL)
    if objs:
        candidate = "[" + ",".join(objs) + "]"
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError("JSON parse error from LLM, first 500 chars:\n" + s[:500])


def call_llm(batch):
    """
    batch: список словарей {"id": int, "text": str}
    возвращает dict[id] -> {"keep": bool, "clean": str}
    """
    user_payload = {"phrases": batch}

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        "temperature": 0.0,
    }

    # --- основная попытка запроса ---
    while True:
        try:
            resp = SESSION.post(
                f"{BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json=payload,
                timeout=120,
            )
        except Exception as e:
            print("[LLM ERROR] request failed, retrying:", e)
            time.sleep(5)
            continue

        if resp.status_code == 200:
            break

        print("[LLM ERROR] HTTP", resp.status_code, resp.text[:200])
        time.sleep(5)

    data = resp.json()
    raw_content = data["choices"][0]["message"]["content"].strip()

    # --- пробуем распарсить батч целиком ---
    try:
        arr = safe_parse_json(raw_content)
    except Exception as e:
        print("[JSON ERROR] batch-level error:", e)
        print("[JSON ERROR] falling back to per-item evaluation…")

        # === Индивидуальная обработка каждого элемента ===
        results = {}
        for obj in batch:
            single_payload = {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": json.dumps({"phrases": [obj]}, ensure_ascii=False),
                    },
                ],
                "temperature": 0.0,
            }

            ok = False
            for attempt in range(3):
                try:
                    r = SESSION.post(
                        f"{BASE_URL}/chat/completions",
                        headers={"Authorization": f"Bearer {API_KEY}"},
                        json=single_payload,
                        timeout=120,
                    )
                    if r.status_code != 200:
                        time.sleep(2)
                        continue

                    c = r.json()["choices"][0]["message"]["content"].strip()
                    parsed = safe_parse_json(c)
                    item = parsed[0]
                    results[obj["id"]] = {
                        "keep": bool(item.get("keep", False)),
                        "clean": (item.get("clean") or "").strip(),
                    }
                    ok = True
                    break
                except Exception:
                    time.sleep(1)

            if not ok:
                results[obj["id"]] = {
                    "keep": False,
                    "clean": "",
                }

        return results

    # --- JSON нормальный ---
    result = {}
    for item in arr:
        idx = int(item["id"])
        result[idx] = {
            "keep": bool(item.get("keep", False)),
            "clean": (item.get("clean") or "").strip(),
        }
    return result


# ==========================
#   MAIN
# ==========================


def main():
    OUTPUT_TEXT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_META.parent.mkdir(parents=True, exist_ok=True)

    resume_from = load_checkpoint()
    print("Resume from source line:", resume_from)

    mode = "a" if resume_from >= 0 and OUTPUT_TEXT.exists() else "w"

    with SOURCE_CORPUS.open("r", encoding="utf-8") as inp, \
            OUTPUT_TEXT.open(mode, encoding="utf-8") as out_txt, \
            OUTPUT_META.open(mode, encoding="utf-8") as out_meta:

        batch_records = []   # список (line_no, phrase)
        batch_for_llm = []   # список {"id": local_id, "text": phrase}
        batch_chars = 0
        last_line_no = resume_from
        batch_counter = 0

        for line_no, line in enumerate(tqdm(inp, desc="scanning corpus")):
            # пропускаем уже обработанные строки
            if line_no <= resume_from:
                continue

            phrase = line.rstrip("\n")
            if not phrase:
                continue

            # ограничиваем длину одной строки
            if len(phrase) > MAX_CHARS_PER_LINE:
                phrase = phrase[:MAX_CHARS_PER_LINE]

            local_id = len(batch_for_llm)
            batch_records.append((line_no, phrase))
            batch_for_llm.append({"id": local_id, "text": phrase})
            batch_chars += len(phrase)
            last_line_no = line_no

            if len(batch_for_llm) >= BATCH_SIZE or batch_chars >= MAX_CHARS_PER_BATCH:
                try:
                    decisions = call_llm(batch_for_llm)
                except Exception as e:
                    print("[JSON ERROR] batch failed, skipping batch:", str(e)[:200])
                    decisions = {
                        obj["id"]: {
                            "keep": False,
                            "clean": "",
                        }
                        for obj in batch_for_llm
                    }

                kept = sum(1 for d in decisions.values() if d["keep"])
                print(
                    f"[info] batch #{line_no // max(1, BATCH_SIZE)}: "
                    f"kept {kept} of {len(batch_for_llm)}"
                )

                for idx_in_batch, (ln, orig_phrase) in enumerate(batch_records):
                    dec = decisions.get(idx_in_batch)
                    if dec and dec["keep"]:
                        clean = dec.get("clean", "").strip()
                        if not clean:
                            continue

                        # текстовый корпус
                        out_txt.write(clean + "\n")

                        # метаинформация для БД
                        meta = {
                            "line_no": ln,
                            "orig": orig_phrase,
                            "clean": clean,
                            "llm_keep": True,
                        }
                        out_meta.write(
                            json.dumps(meta, ensure_ascii=False) + "\n"
                        )

                batch_counter += 1
                if batch_counter % 50 == 0:
                    out_txt.flush()
                    out_meta.flush()
                    os.fsync(out_txt.fileno())
                    os.fsync(out_meta.fileno())

                if last_line_no >= 0:
                    save_checkpoint(last_line_no)

                batch_records.clear()
                batch_for_llm.clear()
                batch_chars = 0

        # хвостовый батч
        if batch_for_llm:
            try:
                decisions = call_llm(batch_for_llm)
            except Exception as e:
                print("[JSON ERROR] tail batch failed, skipping:", str(e)[:200])
                decisions = {
                    obj["id"]: {
                        "keep": False,
                        "clean": "",
                    }
                    for obj in batch_for_llm
                }

            for idx_in_batch, (ln, orig_phrase) in enumerate(batch_records):
                dec = decisions.get(idx_in_batch)
                if dec and dec["keep"]:
                    clean = dec.get("clean", "").strip()
                    if not clean:
                        continue

                    out_txt.write(clean + "\n")
                    meta = {
                        "line_no": ln,
                        "orig": orig_phrase,
                        "clean": clean,
                        "llm_keep": True,
                    }
                    out_meta.write(json.dumps(meta, ensure_ascii=False) + "\n")

        # финальный flush/fsync
        out_txt.flush()
        out_meta.flush()
        os.fsync(out_txt.fileno())
        os.fsync(out_meta.fileno())

        if last_line_no >= 0:
            save_checkpoint(last_line_no)

    print("Clean corpus written to:", OUTPUT_TEXT.resolve())
    print("Meta index written to:", OUTPUT_META.resolve())


if __name__ == "__main__":
    main()
