# hablai-mt

pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu130
pip install transformers psycopg2-binary tqdm python-dotenv

ALTER TABLE public.phrases
    ADD COLUMN phrase_en text;

тест
python translate_phrases_nllb.py --env-file .env --dry-run --batch-size 64 --max-rows 200

сбросить всё, что перевели
UPDATE public.phrases
SET phrase_en = NULL;


(.venv) ol@d7750:~/nvme512/hablai-mt$ python translate_phrases_nllb.py --env-file .env --batch-size 128 --max-rows 0
Loaded .env from .env
Connecting to DB with DSN: dbname=hablai user=hablai password=manager host=localhost port=5432
Loading tokenizer: facebook/nllb-200-distilled-600M
Loading model: facebook/nllb-200-distilled-600M
294816rows [09:34, 512.90rows/s]
Done. processed=294816

список криво переведенного
SELECT *
FROM public.phrases
WHERE phrase_en IS NOT NULL
  AND lower(phrase_en) = lower(phrase);

Изменяем внешний ключ, чтобы можно было каскадно удалить
ALTER TABLE phrase_words
DROP CONSTRAINT phrase_words_phrase_id_fkey;

ALTER TABLE phrase_words
ADD CONSTRAINT phrase_words_phrase_id_fkey
FOREIGN KEY (phrase_id)
REFERENCES public.phrases(id)
ON DELETE CASCADE;

удаляем криво переведенное
DELETE FROM public.phrases
WHERE lower(phrase) = lower(phrase_en)
   OR phrase_en IS NULL AND phrase ~ '^[^a-zA-Záéíóúñü0-9]+$';