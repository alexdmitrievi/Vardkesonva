# Архитектура n8n для юр‑документооборота и календаря в РФ (152‑ФЗ)

## 1) Целевая архитектура решения
- n8n (self-hosted, РФ), PostgreSQL, Nextcloud/ownCloud (WebDAV), Telegram Bot API, календарь РФ (Яндекс 360/CalDAV).
- Доступ только по VPN/allowlist, отдельные учётные записи, шифрование credentials.

## 2) Workflow #1: Создание дела
- Trigger: Webhook `POST /case/create`
- Шаги: проверка уникальности `case_code` -> INSERT в `cases` -> создание папок
  `/Cases/{case_code}/01_Incoming`, `02_Outgoing`, `03_Evidence` -> INSERT в `case_folders`.
- Данные: `cases`, `case_folders`, `case_deadlines`.

## 3) Workflow #2: Telegram ingest
- Trigger: Telegram Trigger (`message`, `document`, `photo`, `caption`, `callback_query`)
- Шаги: извлечение `case_code` -> проверка прав -> `getFile` -> download binary -> safe filename
  без ПДн -> upload в Nextcloud -> INSERT в `documents` -> ack клиенту.
- Данные: `telegram_users`, `documents`, `document_events`.

## 4) Workflow #3: Календарь и напоминания
- Trigger 1: Webhook `POST /case/event/create`
- Trigger 2: Cron каждые 15 минут
- Шаги: создание события в календаре РФ -> INSERT в `calendar_events` ->
  генерация записей в `reminders_queue` -> рассылка юристу/клиенту (клиенту нейтрально).

## 5) Минимальный набор workflow
1. WF_CASE_CREATE_AND_FOLDERS
2. WF_TELEGRAM_DOCUMENT_INGEST
3. WF_CASE_EVENT_CREATE
4. WF_REMINDER_DISPATCH_CRON
5. WF_ERROR_HANDLER_AND_RETRY
