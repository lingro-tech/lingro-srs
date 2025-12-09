#!/usr/bin/env python3
import json
import random
from pathlib import Path

LEXICON_PATH = Path("data/es.lexicon.A1.json")

# -------------------------------
#  ПРОСТОЙ КОНЪЮГАТОР
# -------------------------------

IRREGULAR_PRESENT = {
    "ser": {
        ("yo",): "soy",
        ("tú",): "eres",
        ("él", "ella"): "es",
        ("nosotros",): "somos",
        ("vosotros",): "sois",
        ("ellos", "ellas"): "son",
    },
    "estar": {
        ("yo",): "estoy",
        ("tú",): "estás",
        ("él", "ella"): "está",
        ("nosotros",): "estamos",
        ("vosotros",): "estáis",
        ("ellos", "ellas"): "están",
    },
    "tener": {
        ("yo",): "tengo",
        ("tú",): "tienes",
        ("él", "ella"): "tiene",
        ("nosotros",): "tenemos",
        ("vosotros",): "tenéis",
        ("ellos", "ellas"): "tienen",
    },
    "ir": {
        ("yo",): "voy",
        ("tú",): "vas",
        ("él", "ella"): "va",
        ("nosotros",): "vamos",
        ("vosotros",): "vais",
        ("ellos", "ellas"): "van",
    },
}

def conj_present_regular(lemma: str, pron: str) -> str:
    """
    Очень грубый конъюгатор для регулярных -ar/-er/-ir в Presente.
    Подходит для A1-прототипа.
    """
    if lemma.endswith("ar"):
        stem, group = lemma[:-2], "ar"
    elif lemma.endswith("er"):
        stem, group = lemma[:-2], "er"
    elif lemma.endswith("ir"):
        stem, group = lemma[:-2], "ir"
    else:
        # оставляем как есть
        return lemma

    endings = {
        "yo":      {"ar": "o",   "er": "o",   "ir": "o"},
        "tú":      {"ar": "as",  "er": "es",  "ir": "es"},
        "él":      {"ar": "a",   "er": "e",   "ir": "e"},
        "ella":    {"ar": "a",   "er": "e",   "ir": "e"},
        "nosotros":{"ar": "amos","er": "emos","ir": "imos"},
        "vosotros":{"ar": "áis", "er": "éis", "ir": "ís"},
        "ellos":   {"ar": "an",  "er": "en",  "ir": "en"},
        "ellas":   {"ar": "an",  "er": "en",  "ir": "en"},
    }

    return stem + endings.get(pron, endings["él"])[group]

def conj_present(lemma: str, pron: str) -> str:
    # нерегулярные
    if lemma in IRREGULAR_PRESENT:
        for persons, form in IRREGULAR_PRESENT[lemma].items():
            if pron in persons:
                return form
    # регулярные
    return conj_present_regular(lemma, pron)

# -------------------------------
#  ГЕНЕРАТОР
# -------------------------------

def load_lexicon():
    data = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
    # можем ограничить объём списков, чтобы не брать совсем редкое
    nouns = data.get("NOUN", [])[:1000]
    verbs = data.get("VERB", [])[:1000]
    adjs  = data.get("ADJ", [])[:500]
    prons = data.get("PRON_SUBJ", [])
    return nouns, verbs, adjs, prons

def choose_noun(nouns):
    return random.choice(nouns)

def choose_verb(verbs):
    return random.choice(verbs)

def choose_adj(adjs):
    return random.choice(adjs)

def choose_pron(prons):
    return random.choice(prons)

def make_sentence_S1(nouns, verbs, adjs, prons):
    # PRON_SUBJ + SER + ADJ
    pron = choose_pron(prons)
    adj  = choose_adj(adjs)
    verbo = "ser"
    vform = conj_present(verbo, pron)
    return f"{pron.capitalize()} {vform} {adj}."

def make_sentence_S2(nouns, verbs, adjs, prons):
    # PRON_SUBJ + TENER + NOUN
    pron = choose_pron(prons)
    noun = choose_noun(nouns)
    verbo = "tener"
    vform = conj_present(verbo, pron)
    return f"{pron.capitalize()} {vform} {noun}."

def make_sentence_S3(nouns, verbs, adjs, prons):
    # ART_DEF + NOUN + SER(3sg) + ADJ
    noun = choose_noun(nouns)
    adj  = choose_adj(adjs)
    # очень грубо: "el" по умолчанию
    art  = "el"
    vform = "es"
    return f"{art.capitalize()} {noun} {vform} {adj}."

def make_sentence_S4(nouns, verbs, adjs, prons):
    # PRON_SUBJ + VERB_REGULAR + NOUN
    pron = choose_pron(prons)
    verb = choose_verb(verbs)
    vform = conj_present(verb, pron)
    noun = choose_noun(nouns)
    return f"{pron.capitalize()} {vform} {noun}."

TEMPLATES = [
    make_sentence_S1,
    make_sentence_S2,
    make_sentence_S3,
    make_sentence_S4,
]

def main(n=50):
    nouns, verbs, adjs, prons = load_lexicon()
    for _ in range(n):
        tmpl = random.choice(TEMPLATES)
        sent = tmpl(nouns, verbs, adjs, prons)
        print(sent)

if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    main(n)


