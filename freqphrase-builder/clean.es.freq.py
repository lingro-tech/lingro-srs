#!/usr/bin/env python3
import sys
from pathlib import Path
from collections import Counter

# ============================================================
#  ИМЕНА ВХОДНОГО И ВЫХОДНОГО ФАЙЛОВ (как переменные)
# ============================================================

INPUT_FILE  = "data/es.freq"             # исходный частотный словарь
OUTPUT_FILE = "data/es.freq.cleaned"      # очищенный частотный словарь

# ============================================================
#  НАСТРОЙКИ
# ============================================================

_ES_LETTERS = set("abcdefghijklmnñopqrstuvwxyzáéíóúü")


def is_good_token(w: str) -> bool:
    if not w:
        return False

    PUNCT_TRASH = {
        ".", ",", "?", "!", "¿", "¡", "...",
        "-", "–", "—", '"', "'", "«", "»",
        "(", ")", "[", "]", "{", "}",
    }
    if w in PUNCT_TRASH:
        return False

    if any(ch.isdigit() for ch in w):
        return False

    if not all(ch in _ES_LETTERS for ch in w):
        return False

    # исключаем одиночные буквы, кроме высокочастотных служебных
    if len(w) == 1 and w not in {"a", "y", "o", "e"}:
        return False

    return True


# ============================================================
#  ОСНОВНОЙ ПРОЦЕСС
# ============================================================

def clean_freq_file(path_in: Path, path_out: Path) -> None:
    counter = Counter()

    with path_in.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                freq_str, token = line.split(maxsplit=1)
            except ValueError:
                continue

            try:
                freq = int(freq_str)
            except ValueError:
                continue

            token_norm = token.strip().lower()

            if not is_good_token(token_norm):
                continue

            counter[token_norm] += freq

    items = sorted(counter.items(), key=lambda kv: kv[1], reverse=True)

    with path_out.open("w", encoding="utf-8") as out:
        for token, freq in items:
            out.write(f"{freq} {token}\n")


# ============================================================
#  ЗАПУСК
# ============================================================

if __name__ == "__main__":
    in_path = Path(INPUT_FILE)
    out_path = Path(OUTPUT_FILE)

    clean_freq_file(in_path, out_path)
    print(f"Done. Output written to: {OUTPUT_FILE}")
