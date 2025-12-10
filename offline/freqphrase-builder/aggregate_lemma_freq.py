#!/usr/bin/env python3
import sys
from pathlib import Path
from collections import Counter


def aggregate_lemma_freq(path_in: Path, path_out: Path) -> None:
    counter = Counter()

    with path_in.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                freq_str, lemma = line.split(maxsplit=1)
            except ValueError:
                continue

            try:
                freq = int(freq_str)
            except ValueError:
                continue

            counter[lemma] += freq

    with path_out.open("w", encoding="utf-8") as out:
        for lemma, freq in counter.most_common():
            out.write(f"{freq} {lemma}\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: aggregate_lemma_freq.py <INPUT_RAW_FILE> <OUTPUT_AGG_FILE>")
        sys.exit(1)

    in_path = Path(sys.argv[1]).resolve()
    out_path = Path(sys.argv[2]).resolve()

    if not in_path.is_file():
        print(f"Input file not found: {in_path}")
        sys.exit(1)

    aggregate_lemma_freq(in_path, out_path)
    print(f"Done. Output written to: {out_path}")
