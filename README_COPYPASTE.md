# Готовый набор для копирования в репозиторий

## Что внутри
- `sql/schema.sql` — SQL-схема PostgreSQL.
- `workflows/WF_CASE_CREATE_AND_FOLDERS.json` — создание дела + папки в Nextcloud.
- `workflows/WF_TELEGRAM_DOCUMENT_INGEST.json` — приём документа из Telegram + запись в БД.
- `workflows/WF_CASE_EVENT_CREATE.json` — создание события по делу + постановка напоминаний.
- `workflows/WF_REMINDER_DISPATCH_CRON.json` — периодическая рассылка напоминаний.

## Как импортировать
1. Выполните `sql/schema.sql` в PostgreSQL.
2. В n8n: **Workflows → Import from File** для каждого JSON из `workflows/`.
3. Создайте credentials с именами:
   - `postgres_main`
   - `nextcloud_webdav`
   - `telegram_main_bot`
   - `yandex_calendar_api`
4. Замените `https://nextcloud.example.ru` и endpoint календаря на ваши реальные URL.
5. Включите workflow после тестов на staging.

## Важно
- Тексты клиентских уведомлений оставлены нейтральными.
- В именах файлов используются обезличенные коды дел.
- Перед production рекомендуется добавить подпись webhook-запросов и retry/error branch.

## Рабочий режим через интерфейс приложения

Проект теперь поддерживает полноценный режим через web-интерфейс (desktop + mobile) с единым backend API:

- `frontend/legal_portal.html` — UI для создания дела, событий, AI-консультации и работы с файлами.
- `backend/app/main.py` — FastAPI backend с API `/api/v1/*`, проксированием в n8n и файловым хранилищем.
- `backend/storage` — локальное файловое хранилище (MVP) + `index.json` метаданных.
- Все конфиги вынесены в `backend/.env`.

Ключевые webhook-пути n8n сохранены без изменений:
- `/webhook/case/create`
- `/webhook/case/event/create`
- `/webhook/ai/legal/consult`

Быстрый запуск в dev:

1. `cp backend/.env.example backend/.env` (или PowerShell: `Copy-Item backend/.env.example backend/.env`)
2. `python -m pip install -r backend/requirements.txt`
3. `uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000`
4. `python -m http.server 8080 --directory frontend`
5. Открыть `http://localhost:8080/legal_portal.html`

Дополнительно:
- Контракт API и smoke-тесты: `docs/API_CONTRACT.md`
- Production-деплой на VPS: `docs/DEPLOY_REGRU_VPS.md`
- Frontend runtime-конфиг: `frontend/config.js` (без правки HTML)
- Линт backend: `python -m ruff check backend/app backend/tests`
