# Lingro SRS – проект

## Назначение

Проект для изучения иностранных языков по фразам (SRS флэшкартами).  
Основная идея: большая база фраз (из субтитров и синтезированных предложений), SRS-логика, веб-интерфейс с авторизацией через Telegram.

## Общая структура репозитория

- backend/ — FastAPI API, авторизация, доступ к БД, SRS-логика.
- frontend/ — веб-интерфейс (Next.js + TypeScript + Tailwind, пока каркас).
- offline/ — оффлайн-пайплайны для корпуса:
  - freqphrase-builder/ — частотный словарь, лемматизация, генерация A1-предложений.
  - subtitle-phrase-miner/ — добыча и фильтрация фраз из субтитров.
  - subtitles-cleaner/ — очистка субтитров.
  - hablai/, mt/, tts/, img/ — дополнительные утилиты (перевод, TTS, генерация картинок и т.д.).
- data/ — данные и дампы.
- infra/ — инфраструктура (docker-compose и т.п.).

## Backend

Путь: backend/

Технологии:
- Python 3
- FastAPI
- (позже) PostgreSQL через SQLAlchemy/SQLModel
- Pydantic v2 + pydantic-settings
- JWT для авторизации

Текущая структура backend/app:

- app/main.py — точка входа FastAPI.
- app/core/config.py — настройки (pydantic-settings), чтение .env.
- app/core/security.py — создание JWT токенов.
- app/api/v1/routes_auth.py — эндпоинт /api/v1/auth/telegram (Telegram login).
- app/schemas/auth.py — Pydantic-схемы для Telegram-auth и ответа с токеном.
- app/services/telegram_auth.py — проверка подписи данных Telegram.
- app/srs_logic.py — SRS-логика (на данный момент может быть в виде заглушек или старого кода, нужно постепенно перенести в services/ и api/).

Временные SRS-эндпоинты определены в main.py:
- GET  /api/v1/srs/next
- POST /api/v1/srs/review

## Frontend

Путь: frontend/

Планируется:
- Next.js (app router)
- TypeScript
- Tailwind CSS
- i18n (несколько языков интерфейса)
- Авторизация через Telegram: фронт берёт данные Login Widget и отправляет их на /api/v1/auth/telegram, получает JWT и хранит его (cookie/LocalStorage).

Сейчас это каркас (папки src/app, src/components и т.д.), реализация ещё не сделана.

## Ожидаемые конвенции для кода

- Для backend:
  - Роуты класть в app/api/v1/*.py.
  - Схемы (Pydantic) — в app/schemas/*.py.
  - Сервисы (бизнес-логика) — в app/services/*.py.
  - Настройки — только через app/core/config.py.
- Для frontend:
  - Компоненты — в src/components.
  - Логика общения с API — в src/lib/apiClient.ts.
  - i18n — в src/lib/i18n и src/locales/.

## Что можно просить у Codex

- Написать/дополнить backend-роуты, схемы и сервисы по этой архитектуре.
- Перенести SRS-логику из app/srs_logic.py в services + api.
- Настроить PostgreSQL (models, db/session, миграции).
- Сгенерировать компоненты фронтенда (страницы, хуки, API-клиент).
- Писать тесты для критичных частей (SRS-движок, auth).

