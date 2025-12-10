#!/usr/bin/env python3
import sys
from pathlib import Path
import csv

# ------------------------------------------------------------
#  ПАРАМЕТРЫ
# ------------------------------------------------------------

# входной файл с частотами лемм: "freq lemma"
INPUT_FILE = "data/es.freq.cleaned.lemma"
# базовое имя для выходных файлов
OUTPUT_PREFIX = "data/es.lemma"


def assign_level(rank: int) -> str:
    """
    Простое разбиение по частотным диапазонам.
    Пороговые значения потом можно подправить.
    """
    if rank <= 800:
        return "A1"
    elif rank <= 2000:
        return "A2"
    elif rank <= 4000:
        return "B1"
    elif rank <= 8000:
        return "B2"
    else:
        return "C"


def build_levels(path_in: Path, out_prefix: Path) -> None:
    # читаем леммы и частоты
    items = []
    total_freq = 0

    with path_in.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                freq_str, lemma = line.split(maxsplit=1)
                freq = int(freq_str)
            except Exception:
                continue

            items.append((lemma, freq))
            total_freq += freq

    # сортировка на всякий случай по убыванию частоты
    items.sort(key=lambda x: x[1], reverse=True)

    # подготовка выходов
    stats_path = out_prefix.parent / (out_prefix.name + ".stats.tsv")
    level_files = {
        "A1": (out_prefix.parent / (out_prefix.name + ".level.A1.txt")).open("w", encoding="utf-8"),
        "A2": (out_prefix.parent / (out_prefix.name + ".level.A2.txt")).open("w", encoding="utf-8"),
        "B1": (out_prefix.parent / (out_prefix.name + ".level.B1.txt")).open("w", encoding="utf-8"),
        "B2": (out_prefix.parent / (out_prefix.name + ".level.B2.txt")).open("w", encoding="utf-8"),
        "C":  (out_prefix.parent / (out_prefix.name + ".level.C.txt")).open("w", encoding="utf-8"),
    }

    # пишем stats.tsv
    with stats_path.open("w", encoding="utf-8", newline="") as stats_f:
        writer = csv.writer(stats_f, delimiter="\t")
        writer.writerow([
            "rank", "lemma", "freq",
            "rel_freq",      # доля от общего числа токенов
            "cum_freq",      # накопленная частота
            "coverage",      # накопленное покрытие (0..1)
            "level",
        ])

        cum = 0
        for rank, (lemma, freq) in enumerate(items, start=1):
            cum += freq
            rel = freq / total_freq
            cov = cum / total_freq
            level = assign_level(rank)

            writer.writerow([rank, lemma, freq, f"{rel:.8f}", cum, f"{cov:.8f}", level])

            # записываем в файл уровня
            level_files[level].write(lemma + "\n")

    # закрываем файловые дескрипторы уровней
    for f in level_files.values():
        f.close()

    print(f"Stats written to: {stats_path}")
    for lvl, f in level_files.items():
        print(f"Level {lvl} list: {out_prefix.name}.level.{lvl}.txt")


if __name__ == "__main__":
    # можно передать свой входной файл и префикс:
    #   python build_lemma_levels.py data/es.freq.cleaned.lemma data/es.lemma
    if len(sys.argv) >= 2:
        INPUT = Path(sys.argv[1])
    else:
        INPUT = Path(INPUT_FILE)

    if len(sys.argv) >= 3:
        PREFIX = Path(sys.argv[2])
    else:
        PREFIX = Path(OUTPUT_PREFIX)

    if not INPUT.is_file():
        print(f"Input file not found: {INPUT}")
        sys.exit(1)

    build_levels(INPUT, PREFIX)
