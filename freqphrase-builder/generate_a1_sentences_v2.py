#!/usr/bin/env python3
import json
import random
from pathlib import Path

# ==========================================
#  PATHS
# ==========================================

LEXICON_PATH     = Path("data/es.lexicon.A1.json")
NOUN_MORPH_PATH  = Path("data/es.nouns.A1.morph.json")
ADJ_MORPH_PATH   = Path("data/es.adj.A1.morph.json")

# ==========================================
#  VERB CONJUGATION (PRESENTE)
# ==========================================

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
    """Грубое спряжение регулярных -ar/-er/-ir в Presente."""
    if lemma.endswith("ar"):
        stem, group = lemma[:-2], "ar"
    elif lemma.endswith("er"):
        stem, group = lemma[:-2], "er"
    elif lemma.endswith("ir"):
        stem, group = lemma[:-2], "ir"
    else:
        return lemma  # оставляем как есть

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

    person_endings = endings.get(pron, endings["él"])
    return stem + person_endings[group]

def conj_present(lemma: str, pron: str) -> str:
    """Спряжение: нерегулярные + регулярные."""
    if lemma in IRREGULAR_PRESENT:
        for persons, form in IRREGULAR_PRESENT[lemma].items():
            if pron in persons:
                return form
    return conj_present_regular(lemma, pron)

# ==========================================
#  ARTICLES
# ==========================================

def get_def_article(gender: str, number: str) -> str:
    """Определённый артикль по роду/числу."""
    if gender == "Masc" and number == "Sing":
        return "el"
    if gender == "Fem" and number == "Sing":
        return "la"
    if gender == "Masc" and number == "Plur":
        return "los"
    if gender == "Fem" and number == "Plur":
        return "las"
    # fallback
    return "el"

def get_indef_article(gender: str, number: str) -> str:
    """Неопределённый артикль по роду/числу."""
    if gender == "Masc" and number == "Sing":
        return "un"
    if gender == "Fem" and number == "Sing":
        return "una"
    if gender == "Masc" and number == "Plur":
        return "unos"
    if gender == "Fem" and number == "Plur":
        return "unas"
    return "un"

# ==========================================
#  LOAD LEXICON + MORPH
# ==========================================

def load_data():
    lexicon = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
    noun_morph = json.loads(NOUN_MORPH_PATH.read_text(encoding="utf-8"))
    adj_morph  = json.loads(ADJ_MORPH_PATH.read_text(encoding="utf-8"))

    nouns_all = lexicon.get("NOUN", [])
    adjs_all  = lexicon.get("ADJ", [])
    verbs_all = lexicon.get("VERB", [])
    prons     = lexicon.get("PRON_SUBJ", [])

    # оставляем только существительные, для которых есть морфология
    nouns = [n for n in nouns_all if n in noun_morph]
    # только прилагательные, для которых есть морфология
    adjs  = [a for a in adjs_all if a in adj_morph]

    return nouns, verbs_all, adjs, prons, noun_morph, adj_morph

# ==========================================
#  HELPERS: CHOOSERS
# ==========================================

def choose_pron(prons):
    return random.choice(prons)

def choose_noun_with_morph(nouns, noun_morph, number=None):
    """
    Возвращает (surface_form, lemma, gender, number).
    number:
      - 'Sing'/'Plur'
      - None → случайный выбор (чаще Sing).
    """
    lemma = random.choice(nouns)
    info = noun_morph[lemma]
    gender = info.get("gender", "Masc")
    base_number = info.get("number", "Sing")
    plural_form = info.get("plural", lemma + "s")

    if number is None:
        # лёгкий bias в сторону единственного числа
        number = "Sing" if random.random() < 0.7 else "Plur"

    if number == "Sing":
        surface = lemma
    else:
        surface = plural_form

    return surface, lemma, gender, number

def choose_adj_for(gender: str, number: str, adjs, adj_morph):
    """Выбор прилагательного и правильной формы по роду/числу."""
    lemma = random.choice(adjs)
    forms = adj_morph[lemma]

    key = None
    if gender == "Masc" and number == "Sing":
        key = "m_sg"
    elif gender == "Fem" and number == "Sing":
        key = "f_sg"
    elif gender == "Masc" and number == "Plur":
        key = "m_pl"
    elif gender == "Fem" and number == "Plur":
        key = "f_pl"

    surface = forms.get(key, lemma)
    return surface, lemma

def choose_verb(verbs):
    return random.choice(verbs)

# ==========================================
#  TEMPLATES
# ==========================================

def tmpl_S1(nouns, verbs, adjs, prons, noun_morph, adj_morph):
    """
    S1: ART_DEF + NOUN + SER + ADJ
        El niño es pequeño.
        La casa es grande.
        Los amigos son buenos.
    """
    noun_surface, lemma_n, gender, number = choose_noun_with_morph(
        nouns, noun_morph, number=None
    )
    art = get_def_article(gender, number)
    adj_surface, _ = choose_adj_for(gender, number, adjs, adj_morph)

    # SER 3sg/3pl
    verb = "ser"
    if number == "Sing":
        vform = "es"
    else:
        vform = "son"

    sent = f"{art.capitalize()} {noun_surface} {vform} {adj_surface}."
    return sent

def tmpl_S2(nouns, verbs, adjs, prons, noun_morph, adj_morph):
    """
    S2: PRON_SUBJ + TENER + ART_INDEF + NOUN(Sing)
        Yo tengo un libro.
        Ella tiene una casa.
    """
    pron = choose_pron(prons)
    verb = "tener"
    vform = conj_present(verb, pron)

    noun_surface, lemma_n, gender, number = choose_noun_with_morph(
        nouns, noun_morph, number="Sing"
    )
    art = get_indef_article(gender, "Sing")

    sent = f"{pron.capitalize()} {vform} {art} {noun_surface}."
    return sent

def tmpl_S3(nouns, verbs, adjs, prons, noun_morph, adj_morph):
    """
    S3: PRON_SUBJ + VERB (regular/any) + ART_DEF + NOUN(Sing)
        Ella usa el teléfono.
        Nosotros visitamos la ciudad.
    """
    pron = choose_pron(prons)
    verb = choose_verb(verbs)
    vform = conj_present(verb, pron)

    noun_surface, lemma_n, gender, number = choose_noun_with_morph(
        nouns, noun_morph, number="Sing"
    )
    art = get_def_article(gender, "Sing")

    sent = f"{pron.capitalize()} {vform} {art} {noun_surface}."
    return sent

def tmpl_S4(nouns, verbs, adjs, prons, noun_morph, adj_morph):
    """
    S4: ART_DEF + NOUN + SER + ADJ (PLURAL)
        Los niños son pequeños.
        Las casas son nuevas.
    """
    # принудительно множественное число
    noun_surface, lemma_n, gender, number = choose_noun_with_morph(
        nouns, noun_morph, number="Plur"
    )
    art = get_def_article(gender, "Plur")
    adj_surface, _ = choose_adj_for(gender, "Plur", adjs, adj_morph)

    vform = "son"  # ser 3pl

    sent = f"{art.capitalize()} {noun_surface} {vform} {adj_surface}."
    return sent

TEMPLATES = [tmpl_S1, tmpl_S2, tmpl_S3, tmpl_S4]

# ==========================================
#  MAIN
# ==========================================

def main(n_sentences: int = 50):
    nouns, verbs, adjs, prons, noun_morph, adj_morph = load_data()

    if not nouns or not adjs or not verbs or not prons:
        print("Lexicon/morph data seems incomplete.")
        return

    for _ in range(n_sentences):
        tmpl = random.choice(TEMPLATES)
        sent = tmpl(nouns, verbs, adjs, prons, noun_morph, adj_morph)
        print(sent)

if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    main(n)
