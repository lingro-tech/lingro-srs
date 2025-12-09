# freqphrase-builder

python clean.es.freq.py - очистка частотного словаря

pip install stanza
python3 - << 'EOF'
import stanza
stanza.download("es")   # скачивает модель Spanish UD (2024–2025)
EOF

head -n 100000 data/es.freq.cleaned > data/es.freq.cleaned.100000
/usr/bin/time -v /home/ol/_p/freqphrase-builder/data/.venv/bin/python /home/ol/_p/freqphrase-builder/lemmatize.es.freq.cleaned.sample.py data/es.freq.cleaned.100000

cd data
split -n l/10 es.freq.cleaned part_
ls part_* | parallel -j 10 'python ../lemmatize.es.freq.cleaned.py {}'



cat part_*.lemma > es.freq.cleaned.lemma.raw
python ../aggregate_lemma_freq.py es.freq.cleaned.lemma.raw es.freq.cleaned.lemma
# data/es.freq.cleaned.lemma

python ../aggregate_lemma_forms.py es.freq.cleaned.lemma.forms.json part_*.lemma.forms.json
# data/es.freq.cleaned.lemma.forms.json

Скрипт: построение рангов и уровней (build_lemma_levels.py)
Вход: es.freq.cleaned.lemma (формат freq lemma)
Выходы:
es.lemma.stats.tsv — полный список с статистикой и уровнем
es.lemma.level.A1.txt, A2, B1, B2 — списки лемм по уровням
Пороговые значения уровней можно будет потом подогнать. Сейчас беру разумные диапазоны по рангу:
A1: 1–800
A2: 801–2000
B1: 2001–4000
B2: 4001–8000
остальное: C (если понадобится)

/home/ol/_p/freqphrase-builder/data/.venv/bin/python /home/ol/_p/freqphrase-builder/build_lemma_levels.py
# Stats written to: data/es.lemma.stats.tsv
# Level A1 list: es.lemma.level.A1.txt
# Level A2 list: es.lemma.level.A2.txt
# Level B1 list: es.lemma.level.B1.txt
# Level B2 list: es.lemma.level.B2.txt
# Level C list: es.lemma.level.C.txt

Дальше логика такая:
Из готовых частотных лемм делаем лексикон A1 по частям речи.
Определяем шаблоны предложений A1.
Набрасываем прототип генератора фраз A1.
1. Лексикон A1 по частям речи
Берём es.freq.cleaned.lemma + es.freq.cleaned.lemma.forms.json.
Цель: получить списки:
A1_NOUNS
A1_VERBS
A1_ADJS
A1_ADVS
A1_PRON_SUBJ (личные местоимения)
Скрипт 1: разметка A1-лемм по POS
Файл build_a1_lexicon.py:

python3 build_a1_lexicon.py
# Written lexicon to data/es.lexicon.A1.json

# {
#  "NOUN": ["tiempo", "persona", "año", ...],
#  "VERB": ["ser", "estar", "tener", "hacer", ...],
#  "ADJ": ["bueno", "nuevo", "mismo", ...],
#  "ADV": ["muy", "bien", ...],
#  "PRON_SUBJ": ["yo", "tú", "él", "ella", ...]
# }

2. Базовые шаблоны A1
Определим несколько простых, «учебных» схем (только настоящее время, простые конструкции):
S1:
PRON_SUBJ + VERB_SER + ADJ
– «Ella es feliz.»
S2:
PRON_SUBJ + VERB_TENER + NOUN
– «Yo tengo tiempo.»
S3:
ART_DEF + NOUN + VERB_SER_3SG + ADJ
– «La casa es grande.»
S4:
PRON_SUBJ + VERB_REGULAR (present 1sg/3sg) + NOUN
– «Yo estudio español.» / «Ella usa el teléfono.»
S5:
PRON_SUBJ + ESTAR + GERUNDIO (ограниченно)
– «Estoy leyendo.»
Для прототипа мы ограничимся S1–S4, потому что они легко реализуются простым конъюгатором.

3. Прототип генератора A1-фраз
Сделаем:
очень простой конъюгатор настоящего времени для регулярных глаголов -ar/-er/-ir,
таблицу основных нерегулярных (ser, estar, tener, ir, hacer, poder, querer — можно расширять),
генератор, который:
грузит es.lexicon.A1.json,
выбирает случайные леммы,
конъюгирует их,
собирает предложения по шаблонам S1–S4.
Файл generate_a1_sentences.py:

python3 generate_a1_sentences.py 50
# Ella es importante.
# Yo tengo tiempo.
# El problema es grande.
# Nosotros estudiamos español.
# Tú tienes dinero.
# El niño es pequeño.

Это уже:
опирается на частотный A1-лексикон,
использует простейшую морфологию,
даёт грамматически приемлемые A1-предложения (не идеальные, но достаточно близко).

Сейчас у нас есть:
Очищенный словарь (es.freq.cleaned)
Лемматизированный словарь (es.freq.cleaned.lemma)
Карта форм (lemma_forms.json)
Частотные уровни (es.lemma.level.*)
A1-лексикон (es.lexicon.A1.json)
Прототип генератора (без учёта рода, числа, правильных артиклей, правильных сочетаний глагол–аргумент и т.д.)
Теперь — делаем качественный A1-генератор, пригодный для учебного корпуса.

ЗАДАЧА НА ЭТОТ ШАГ
Добавляем в генератор корректные артикли (el/la), множественное число и согласование прилагательных.
Без этих механик невозможно создавать даже минимально корректный корпус A1.
ПЛАН ШАГА
1) Создать словарь существительных → род + число
Нам нужен файл:
noun → {"gender": "m/f", "plural": <форма множественного числа>}

Мы можем сделать это автоматически через Stanza:
определить UPOS = NOUN
прочитать морфологические признаки:
Gender=Masc|Fem
Number=Sing|Plur
Если слово стоит в единственном числе, мы получим его род.
А множественное число можно сгенерировать правилом:
если оканчивается на гласную → +s
на согласную → +es
исключения (lápiz → lápices) можно добавить позже.
Будем строить словарь только для A1_NOUNS.
2) Создать словарь прилагательных → формы согласования
Для каждого прилагательного A1:
азовая форма: masculino/singular
femenino: обычно замена o → a
plural: +s или +es
Опять же, Stanza нам даст род/число в формах, встречающихся в корпусе.
Строим структуру:
# adj → {
#  "m_sg": "grande",
#  "f_sg": "grande",
#  "m_pl": "grandes",
#  "f_pl": "grandes"
# }
Для окончания -o/-a — делаем точные формы.
Для -e, -l, -r — одинаковый род, разные числа.
Это 95% случаев A1.

3) Обновляем шаблоны генерации
Теперь создадим шаблоны, которые учитывают:
выбор рода (m/f)
выбор числа (sg/pl)
корректную форму артикля
корректную форму прилагательного
Например:
S1 (улучшенная):
ART + NOUN + SER + ADJ
Где:
ART ∈ {el, la, los, las}
NOUN имеет род+число
ADJ согласовано в роде+числе

4) Обновляем генератор, создаём полноценные A1-предложения
После этого мы сможем:
генерировать тысячи корректных A1 предложений;
получать гораздо более естественные данные для SRS;
масштабировать на A2–B2, подставляя более сложные структуры.

НИЖЕ — КОД ДЛЯ ЭТОГО ШАГА
(1) генерация словаря NOUN → gender/number/plural
(2) генерация словаря ADJ → формы согласования
1. Скрипт: создание морфословаря существительных A1
build_noun_morph.py
# Written: data/es.nouns.A1.morph.json
2. Скрипт: создание морфословаря прилагательных A1
build_adj_morph.py
# Written: data/es.adj.A1.morph.json

После запуска двух скриптов
В data/ появятся:
es.nouns.A1.morph.json
es.adj.A1.morph.json
Теперь у нас есть полноценная морфология A1:
правильный род, число, множественные формы,
согласование прилагательных,
артикли мы легко подстроим под gender/number:
m sg → el
f sg → la
m pl → los
f pl → las

Делаем полноценный генератор A1-фраз с согласованием артикля и прилагательного.
Ниже один скрипт generate_a1_sentences_v2.py, который:
грузит
data/es.lexicon.A1.json
data/es.nouns.A1.morph.json
data/es.adj.A1.morph.json
генерирует A1-предложения по 4 шаблонам с учётом рода/числа.

python3 generate_a1_sentences_v2.py 50
