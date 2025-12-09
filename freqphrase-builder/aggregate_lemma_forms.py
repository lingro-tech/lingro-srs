#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from collections import Counter, defaultdict


def aggregate_lemma_forms(output_path: Path, input_paths) -> None:
    lemma_forms = defaultdict(Counter)

    for p in input_paths:
        p = Path(p).resolve()
        if not p.is_file():
            print(f"Skipping missing file: {p}")
            continue

        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)

        for lemma, forms in data.items():
            for form, freq in forms.items():
                lemma_forms[lemma][form] += int(freq)

    with output_path.open("w", encoding="utf-8") as out:
        json.dump(
            {lemma: dict(forms) for lemma, forms in lemma_forms.items()},
            out,
            ensure_ascii=False,
            indent=2,
        )


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: aggregate_lemma_forms.py <OUTPUT_JSON> <INPUT_JSON_1> [<INPUT_JSON_2> ...]")
        sys.exit(1)

    out_path = Path(sys.argv[1]).resolve()
    in_paths = sys.argv[2:]

    aggregate_lemma_forms(out_path, in_paths)
    print(f"Done. Output written to: {out_path}")
