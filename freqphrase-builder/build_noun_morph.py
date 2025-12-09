#!/usr/bin/env python3
import sys
import json
from pathlib import Path
import stanza

LEXICON_A1 = Path("data/es.lexicon.A1.json")
OUT_FILE = Path("data/es.nouns.A1.morph.json")

stanza.download("es", verbose=False)
nlp = stanza.Pipeline("es", processors="tokenize,pos,lemma", tokenize_no_ssplit=True)

def detect_gender_number(word: str):
    doc = nlp(word)
    try:
        w = doc.sentences[0].words[0]
        if w.upos != "NOUN":
            return None
        feats = w.feats or ""
        gender = None
        number = None
        for part in feats.split("|"):
            if part.startswith("Gender="):
                gender = part.split("=")[1]
            if part.startswith("Number="):
                number = part.split("=")[1]
        return gender, number
    except:
        return None

def make_plural(word: str):
    # базовые правила A1
    if word.endswith(("a", "e", "i", "o", "u")):
        return word + "s"
    return word + "es"

def main():
    data = json.loads(LEXICON_A1.read_text(encoding="utf-8"))
    nouns = data.get("NOUN", [])

    result = {}

    for noun in nouns:
        g_n = detect_gender_number(noun)
        if not g_n:
            continue
        gender, number = g_n
        plural_form = make_plural(noun)
        result[noun] = {
            "gender": gender,
            "number": number,
            "plural": plural_form
        }

    OUT_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Written: {OUT_FILE}")

if __name__ == "__main__":
    main()
