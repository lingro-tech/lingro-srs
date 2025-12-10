#!/usr/bin/env python3
import sys
from pathlib import Path
import json
import stanza

# Вход
LEMMA_LEVEL_A1 = Path("data/es.lemma.level.A1.txt")
OUT_LEXICON = Path("data/es.lexicon.A1.json")

# Инициализация Stanza только с POS/lemma
stanza.download("es", verbose=False)
nlp = stanza.Pipeline(
    lang="es",
    processors="tokenize,pos,lemma",
    tokenize_no_ssplit=True,
)

def detect_pos(lemma: str) -> str | None:
    doc = nlp(lemma)
    try:
        return doc.sentences[0].words[0].upos  # 'NOUN', 'VERB', 'ADJ', ...
    except Exception:
        return None

def main():
    if not LEMMA_LEVEL_A1.is_file():
        print(f"Missing {LEMMA_LEVEL_A1}")
        sys.exit(1)

    pos_buckets: dict[str, list[str]] = {}

    with LEMMA_LEVEL_A1.open("r", encoding="utf-8") as f:
        for line in f:
            lemma = line.strip()
            if not lemma:
                continue
            upos = detect_pos(lemma)
            if not upos:
                continue
            pos_buckets.setdefault(upos, []).append(lemma)

    # добавим вручную базовые местоимения (A1)
    pos_buckets.setdefault("PRON_SUBJ", [])
    pos_buckets["PRON_SUBJ"].extend(
        ["yo", "tú", "él", "ella", "nosotros", "vosotros", "ellos", "ellas"]
    )

    with OUT_LEXICON.open("w", encoding="utf-8") as out:
        json.dump(pos_buckets, out, ensure_ascii=False, indent=2)

    print(f"Written lexicon to {OUT_LEXICON}")

if __name__ == "__main__":
    main()
