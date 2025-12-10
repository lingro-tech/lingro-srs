#!/usr/bin/env python3
import sys
from pathlib import Path
from collections import Counter, defaultdict
import json
import stanza

# ============================================================
#  LOAD STANZA (Spanish UD 2024–2025)
# ============================================================

stanza.download("es", verbose=False)
nlp = stanza.Pipeline(
    lang="es",
    processors="tokenize,pos,lemma",
    tokenize_no_ssplit=True,
)


# ============================================================
#  PROCESS TOKEN-BY-TOKEN
# ============================================================

def process_token(token: str) -> str:
    """Получает лемму через Stanza."""
    doc = nlp(token)
    # doc содержит 1 предложение, 1 токен
    try:
        return doc.sentences[0].words[0].lemma
    except Exception:
        return token  # fallback: если модель ошиблась


def lemmatize_freq_file(path_in: Path, path_lemma: Path, path_forms: Path) -> None:
    lemma_counter = Counter()
    lemma_forms = defaultdict(Counter)

    with path_in.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                freq_str, word = line.split(maxsplit=1)
            except ValueError:
                continue

            try:
                freq = int(freq_str)
            except ValueError:
                continue

            lemma = process_token(word)

            lemma_counter[lemma] += freq
            lemma_forms[lemma][word] += freq

    # ==============================
    #  WRITE LEMMA FREQUENCY FILE
    # ==============================

    with path_lemma.open("w", encoding="utf-8") as out:
        for lemma, freq in lemma_counter.most_common():
            out.write(f"{freq} {lemma}\n")

    # ==============================
    #  WRITE LEMMA → FORMS MAP
    # ==============================

    with path_forms.open("w", encoding="utf-8") as out:
        json.dump(
            {lemma: dict(forms) for lemma, forms in lemma_forms.items()},
            out,
            ensure_ascii=False,
            indent=2,
        )


# ============================================================
#  MAIN
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: lemmatize_freq_es.py <INPUT_FREQ_FILE>")
        sys.exit(1)

    input_path = Path(sys.argv[1]).resolve()

    if not input_path.is_file():
        print(f"Input file not found: {input_path}")
        sys.exit(1)

    # Папка такая же, как у входного файла
    out_dir = input_path.parent

    # К имени источника добавляем признак лемматизации
    # Примеры:
    #   es.freq.cleaned           -> es.freq.cleaned.lemma
    #   es.freq.cleaned           -> es.freq.cleaned.lemma.forms.json
    lemma_freq_path = out_dir / f"{input_path.name}.lemma"
    lemma_forms_path = out_dir / f"{input_path.name}.lemma.forms.json"

    lemmatize_freq_file(input_path, lemma_freq_path, lemma_forms_path)

    print("Done.")
    print(f"Lemma frequency file: {lemma_freq_path}")
    print(f"Lemma→forms map:       {lemma_forms_path}")
