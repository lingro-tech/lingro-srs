# hablai-app

uvicorn app_srs:app --host 192.168.1.66 --port 8000 --reload

Проверка в браузере:
http://192.168.1.66:8000/
http://localhost:8000/ – заглушка,
http://192.168.1.66:8000/api/next_phrase?user_id=1 – получить следующую фразу.

Пример запроса ответа (из терминала):
curl -X POST http://localhost:8000/api/answer \
  -H "Content-Type: application/json" \
  -d '{"user_id":1, "phrase_id":123, "answer_color":"green"}'