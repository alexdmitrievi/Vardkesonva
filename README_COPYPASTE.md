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
