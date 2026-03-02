# Готовый набор для запуска без БД (n8n + Google Sheets)

## Что внутри
- `workflows/WF_UNIFIED_LEGAL_AUTOMATION.json` — единый workflow для импорта одним файлом в n8n Cloud/UI.
- `workflows/WF_CASE_CREATE_AND_FOLDERS.json` — создание дела + папки в Nextcloud + запись в Google Sheets.
- `workflows/WF_TELEGRAM_DOCUMENT_INGEST.json` — приём документа из Telegram + загрузка в Nextcloud + запись в Google Sheets.
- `workflows/WF_CASE_EVENT_CREATE.json` — создание события по делу + запись в Google Sheets.
- `workflows/WF_REMINDER_DISPATCH_CRON.json` — cron‑рассылка напоминаний на основе Google Sheets.
- `n8n_legal_russia_architecture.md` — архитектура и ограничения варианта без БД.

## Как импортировать
1. Рекомендуется: в n8n **Workflows → Import from File** и выбрать `workflows/WF_UNIFIED_LEGAL_AUTOMATION.json`.
2. Альтернатива: импортировать по одному `WF_*.json`.
2. Создайте credentials:
   - `nextcloud_webdav`
   - `telegram_main_bot`
   - `yandex_calendar_api`
   - `google_sheets_main`
3. В Google Sheets создайте листы:
   - `дела`
   - `папки_дел`
   - `документы`
   - `события_календаря`
   - `напоминания`
   - `журнал_отправки_напоминаний`
4. Замените плейсхолдеры URL (`nextcloud.example.ru`, endpoint календаря).

> Примечание: `ALL_WORKFLOWS_BUNDLE.json` — это массив workflow-объектов. В ряде версий n8n Cloud импорт из редактора может не отрисовать его как один workflow. Используйте `WF_UNIFIED_LEGAL_AUTOMATION.json` для надёжного импорта одним файлом.


## Какие данные именно брать из виртуальной машины (Yandex Cloud)
Короткий ответ: **напрямую из строки VM в ноды почти ничего не вставляется**, кроме адресов ваших сервисов, которые крутятся на этой VM.

Что из VM реально нужно:

1) **Публичный IP или домен VM**
- нужен для доступа к вашим сервисам (n8n, Nextcloud, ваш API).
- примеры, куда вставлять:
  - в Nextcloud нодах (`DAV MKCOL...`, `DAV Upload`) вместо `nextcloud.example.ru`;
  - во внешние системы как webhook base URL n8n (если n8n стоит на этой VM);
  - в `YC_METADATA_API_URL`, если mirror API у вас на этой VM.

2) **Порты сервисов на VM**
- обычно: `5678` (n8n), `443/80` (через reverse proxy), ваш порт API (например `8000`).
- в ноды порты вручную не вносятся, но должны быть корректно отражены в URL, который вы вставляете.

3) **Ничего из внутренних полей VM типа `Внутренний IPv4`, `vCPU`, `RAM` в ноды не вставляется**
- это инфраструктурные параметры, не параметры workflow.

---

### Мини‑чеклист «что вставить куда»
- В ноды Nextcloud (`DAV ...`) → URL вашего Nextcloud на VM + credential `nextcloud_webdav`.
- В webhook-ноды ничего вручную не вставляете, но копируете их **Production URL** и вставляете во внешнюю систему.
- В `YC_METADATA_API_URL` (Variables) → URL вашего API на VM, например `https://<ваш-домен>/api`.
- В `GSHEET_ID` → только ID таблицы Google Sheets (не связан с VM).
- В Telegram/Calendar credentials → токены/ключи сервисов (не из VM-строки).

Если у вас сейчас только VM без домена:
- временно можно использовать публичный IP,
- для production лучше домен + HTTPS (Nginx/Caddy + сертификат).

## Конкретно по вашим скриншотам VM: что копировать и куда вставлять
Из ваших данных видно:
- Публичный IPv4: `158.160.191.139`
- Внутренний IPv4: `10.130.0.6`
- SSH команда: `ssh -l vardkesovna 158.160.191.139`
- Публичный IP сейчас **динамический**.

### Копируем и вставляем
1. **Публичный IPv4 `158.160.191.139`**
   - В URL нод Nextcloud (`DAV MKCOL Incoming/Outgoing/Evidence`, `DAV Upload`) — **если Nextcloud у вас на этой VM**.
   - В `YC_METADATA_API_URL` (Variables) — **если ваш API mirror на этой VM**.
   - Во внешнюю систему, которая вызывает webhook, как base домен n8n — **если n8n на этой VM**.

2. **Production URL из webhook-нод**
   - Берёте прямо в нодах `Webhook Case Create` и `Webhook Event` (вкладка Production URL).
   - Эти URL вставляете в CRM/сайт/форму, которая отправляет POST-запросы.
   - IP VM в webhook-ноду вручную не вставляется, он уже входит в URL вашего n8n-домена/хоста.

### НЕ копируем в ноды
- `Внутренний IPv4 (10.130.0.6)` — не нужен для внешних webhook и обычно не нужен в текущих нодах.
- `Идентификатор VM`, `vCPU`, `RAM`, `Зона`, `Группа безопасности` — это инфраструктура, не параметры workflow.
- SSH логин/команда — нужны для администрирования VM, но не для значений в n8n нодах.

### Важный момент по вашему IP
У вас тип публичного IP: **динамический**. Если IP изменится, URL в нодах/внешних сервисах сломаются.
Рекомендуется:
- либо закрепить статический IP,
- либо использовать домен + reverse proxy + HTTPS.

### Как сделать статический IP в Yandex Cloud (чтобы webhook не отваливались)
Если у VM динамический публичный IP, после перезапуска/изменений он может смениться. Тогда URL в webhook и интеграциях сломаются.

Сделайте так (через консоль Yandex Cloud):
1. Откройте **VPC → IP-адреса**.
2. Нажмите **Зарезервировать адрес** (статический).
3. Выберите ту же зону, где ваша VM (у вас `ru-central1-d`).
4. После создания статического IP откройте вашу VM → **Сеть**.
5. В сетевом интерфейсе замените текущий публичный IP на зарезервированный статический.
6. Если используете firewall/security group — убедитесь, что открыты нужные порты (`80/443`, при необходимости `5678`).

После смены IP:
- обновите DNS (если есть домен),
- проверьте, что webhook в внешних системах указывают на актуальный **Production URL**,
- перепроверьте Nextcloud/API URL в нодах, если вы указывали IP напрямую.

Практика для production: домен + HTTPS + статический IP.

## Что импортировать в n8n: `WF_UNIFIED_LEGAL_AUTOMATION.json` или `ALL_WORKFLOWS_BUNDLE.json`?
Коротко:
- Для обычной работы в n8n UI/Cloud импортируйте **`WF_UNIFIED_LEGAL_AUTOMATION.json`**.
- `ALL_WORKFLOWS_BUNDLE.json` — это технический bundle-массив из нескольких workflow-объектов, не один workflow-граф.

Разница:
1. `WF_UNIFIED_LEGAL_AUTOMATION.json`
   - один JSON-объект одного workflow;
   - 4 ветки в одном canvas;
   - самый надёжный вариант для `Import from File`.

2. `ALL_WORKFLOWS_BUNDLE.json`
   - JSON-массив из отдельных `WF_*.json`;
   - полезен как артефакт сборки/резервная упаковка;
   - в части версий n8n может импортироваться не так наглядно, как unified-файл.

Итого: в вашем сценарии нажимайте **Import from File → `WF_UNIFIED_LEGAL_AUTOMATION.json`**.

## Чёткая инструкция: что именно донастроить после импорта

### 1) Сначала создайте переменные окружения в n8n
В `Settings → Variables` добавьте:
- `GSHEET_ID` = ID вашей Google-таблицы (из URL между `/d/` и `/edit`).
- `YC_METADATA_MIRROR` = `0` (или `1`, если включаете зеркалирование в Yandex Cloud).
- `YC_METADATA_API_URL` = `https://<ваш-api-домен>` (нужно только при `YC_METADATA_MIRROR=1`).

---

### 2) Создайте Google Sheets строго с этими листами и колонками
Откройте Google Sheets и создайте 6 листов. В **первой строке** каждого листа укажите заголовки **в таком порядке**:

1. `дела`
   - `код_дела`, `клиент_id`, `юрист_id`, `тип_дела`, `юрисдикция`, `статус`, `создано_в`

2. `папки_дел`
   - `код_дела`, `путь_входящие`, `путь_исходящие`, `путь_доказательства`, `создано_в`

3. `документы`
   - `id_документа`, `код_дела`, `telegram_id_отправителя`, `имя_файла_в_хранилище`, `путь_в_хранилище`, `mime_тип`, `размер_байт`, `загружено_в`

4. `события_календаря`
   - `id_события`, `код_дела`, `тип_события`, `начало`, `конец`, `внешний_id_события`, `создано_в`

5. `напоминания`
   - `id_напоминания`, `id_события`, `роль_получателя`, `telegram_chat_id`, `текст_сообщения`, `отправить_в`, `статус`, `отправлено_в`

6. `журнал_отправки_напоминаний`
   - `id_напоминания`, `отправлено_в`, `роль_получателя`, `статус`

Важно:
- названия листов должны совпадать **буква в букву**;
- названия полей в первой строке должны совпадать **буква в букву**;
- Google credential должен иметь доступ на edit к этой таблице.

Если хотите английские названия — можно, но тогда нужно массово менять `range` и ключи полей во всех Google Sheets/Code-нодах.

---

### 3) Какие ноды с API/URL нужно заполнить руками
После импорта workflow откройте эти ноды и проверьте настройки:

#### A. Nextcloud WebDAV
1. `CASE ... DAV MKCOL Incoming`
2. `CASE ... DAV MKCOL Outgoing`
3. `CASE ... DAV MKCOL Evidence`
4. `INGEST ... DAV Upload`

Что заполнить:
- URL хоста (`nextcloud.example.ru` -> ваш реальный домен);
- credential `nextcloud_webdav` (логин/пароль или app-password Nextcloud);
- при необходимости префикс пути пользователя (`/remote.php/dav/files/<user>/...`).

#### B. Yandex Calendar API
1. `EVENT ... Calendar Create`

Что заполнить:
- URL endpoint календаря (если у вас другой endpoint/шлюз);
- credential `yandex_calendar_api` (обычно Header Auth c Bearer токеном).

#### C. Telegram
1. `INGEST ... Telegram Trigger`
2. `INGEST ... TG Case Not Found`
3. `INGEST ... TG Ack`
4. `REMIND ... TG Send`

Что заполнить:
- credential `telegram_main_bot` с токеном бота;
- убедиться, что бот добавлен/разрешён в нужных чатах.

#### D. Опционально Yandex Cloud mirror (dual-write)
1. `... IF YC Mirror Enabled`
2. `... YC Mirror Case Upsert`
3. `... YC Mirror Event Upsert`
4. `... YC Mirror Document Upsert`
5. `... YC Mirror Reminder Sent`

Что заполнить:
- `YC_METADATA_MIRROR=1`;
- `YC_METADATA_API_URL`;
- credential `yc_backend_api` (HTTP Header Auth, токен вашего backend API).

Если mirror не нужен сейчас — оставьте `YC_METADATA_MIRROR=0`, эти ветки автоматически не активируются.

---

### 3.1) Очень простая настройка по нодам (для новичка, без кода)
Ниже — что открыть и что вставить, буквально по шагам.

#### WF 1: CASE_CREATE_AND_FOLDERS (создание дела)
1. `Webhook Case Create`:
   - ничего не меняйте, просто скопируйте Production URL (понадобится вашему сайту/форме).
2. `GS Read Cases`:
   - Credential: `google_sheets_main`;
   - Sheet ID: `={{$env.GSHEET_ID}}` (не трогать);
   - Range: `дела!A:G`.
3. `DAV MKCOL Incoming`, `DAV MKCOL Outgoing`, `DAV MKCOL Evidence`:
   - URL должен указывать на ваш Nextcloud домен (не `nextcloud.example.ru`);
   - Credential: `nextcloud_webdav`.
4. `GS Append Case` и `GS Append Folders`:
   - Credential: `google_sheets_main`;
   - Range: `дела!A:G` и `папки_дел!A:E`.
5. `IF YC Mirror Enabled` и `YC Mirror Case Upsert`:
   - на старте можно не трогать (работают только если `YC_METADATA_MIRROR=1`).

#### WF 2: TELEGRAM_DOCUMENT_INGEST (приём файлов из Telegram)
1. `Telegram Trigger`:
   - Credential: `telegram_main_bot`.
2. `GS Read Folders`:
   - Range: `папки_дел!A:E`.
3. `TG getFile` и `TG Download`:
   - ничего не менять (берут токен из Telegram credential автоматически).
4. `DAV Upload`:
   - проверьте домен Nextcloud в URL + credential `nextcloud_webdav`.
5. `GS Append Document`:
   - Range: `документы!A:H`.
6. `TG Ack` / `TG Case Not Found`:
   - Credential: `telegram_main_bot`.

#### WF 3: CASE_EVENT_CREATE (события и напоминания)
1. `Webhook Event`:
   - скопируйте Production URL и используйте его в системе, которая создаёт события.
2. `Calendar Create`:
   - URL календаря: ваш рабочий endpoint;
   - Credential: `yandex_calendar_api`.
3. `GS Append Event`:
   - Range: `события_календаря!A:G`.
4. `GS Append Reminder 24h`, `GS Append Reminder 2h`, `GS Append Client Payment Reminder`:
   - Range везде: `напоминания!A:H`.

#### WF 4: REMINDER_DISPATCH_CRON (рассылка напоминаний)
1. `Cron`:
   - интервал сейчас 15 минут (можете изменить).
2. `GS Read Reminders`:
   - Range: `напоминания!A:H`.
3. `GS Read Sent Log` и `GS Sent Log`:
   - Range: `журнал_отправки_напоминаний!A:D`.
4. `TG Send`:
   - Credential: `telegram_main_bot`.

---

## Какие ноды настраиваем, а какие не трогаем
Ниже — правило для первого запуска: **настраиваем только то, где меняются ваши URL/ключи/credentials**, остальное не трогаем.

### 1) В эти ноды заходим и настраиваем

#### CASE_CREATE_AND_FOLDERS
- `Webhook Case Create` — берём Production URL для внешней системы.
- `GS Read Cases` — credential `google_sheets_main`, range `дела!A:G`.
- `DAV MKCOL Incoming` — ваш домен Nextcloud + credential `nextcloud_webdav`.
- `DAV MKCOL Outgoing` — ваш домен Nextcloud + credential `nextcloud_webdav`.
- `DAV MKCOL Evidence` — ваш домен Nextcloud + credential `nextcloud_webdav`.
- `GS Append Case` — credential `google_sheets_main`, range `дела!A:G`.
- `GS Append Folders` — credential `google_sheets_main`, range `папки_дел!A:E`.
- `IF YC Mirror Enabled` / `YC Mirror Case Upsert` — только если включаете mirror (`YC_METADATA_MIRROR=1`).

#### CASE_EVENT_CREATE
- `Webhook Event` — берём Production URL для внешней системы.
- `Calendar Create` — endpoint + credential `yandex_calendar_api`.
- `GS Append Event` — range `события_календаря!A:G`.
- `GS Append Reminder 24h` — range `напоминания!A:H`.
- `GS Append Reminder 2h` — range `напоминания!A:H`.
- `GS Append Client Payment Reminder` — range `напоминания!A:H`.
- `IF YC Mirror Enabled` / `YC Mirror Event Upsert` — только при mirror.

#### REMINDER_DISPATCH_CRON
- `Cron` — при необходимости меняете интервал (по умолчанию 15 минут).
- `GS Read Reminders` — range `напоминания!A:H`.
- `GS Read Sent Log` — range `журнал_отправки_напоминаний!A:D`.
- `TG Send` — credential `telegram_main_bot`.
- `GS Sent Log` — range `журнал_отправки_напоминаний!A:D`.
- `IF YC Mirror Enabled` / `YC Mirror Reminder Sent` — только при mirror.

#### TELEGRAM_DOCUMENT_INGEST
- `Telegram Trigger` — credential `telegram_main_bot`.
- `GS Read Folders` — range `папки_дел!A:E`.
- `DAV Upload` — ваш домен Nextcloud + credential `nextcloud_webdav`.
- `GS Append Document` — range `документы!A:H`.
- `TG Case Not Found` / `TG Ack` — credential `telegram_main_bot`.
- `IF YC Mirror Enabled` / `YC Mirror Document Upsert` — только при mirror.

### 2) В эти ноды обычно НЕ лезем (оставляем как есть)
- Code-ноды:
  - `Check Case Code`, `Build Paths`, `Parse`, `Match Case`, `Safe Filename`, `Prepare`, `Filter Due`.
- Внутренние роутеры/логика:
  - `IF Exists`, `IF Case Missing`, `IF Client Payment Reminder`, `Split`.
- Технические Telegram HTTP-ноды:
  - `TG getFile`, `TG Download`.
- Ответы webhook:
  - `Respond 409`, `Respond 201`.

Если в этих нодах менять поля без необходимости, можно случайно сломать весь поток.

### 3) Простой принцип
- Меняем: **URL, credentials, ranges, переменные окружения**.
- Не меняем: **JS-код, ветвления, внутренние связи и response-ноды**, если нет отдельной задачи на разработку.

---

### 3.2) Как настроить именно эти 2 webhook-ноды (со скриншотов)
Речь про ноды:
- `CASE_CREATE_AND_FOLDERS :: Webhook Case Create`
- `CASE_EVENT_CREATE :: Webhook Event`

Сделайте одинаково по шагам:

#### A. `Webhook Case Create`
1. Откройте ноду → вкладка **Parameters**.
2. Проверьте поля:
   - **HTTP Method**: `POST`
   - **Path**: `case/create`
   - **Authentication**: `None` (минимум для старта)
   - **Respond**: `Using 'Respond to Webhook' Node`
3. Нажмите **Test URL**:
   - для проверки вручную используйте URL вида `/webhook-test/case/create`.
4. Для рабочего режима используйте **Production URL**:
   - URL вида `/webhook/case/create`.
5. Нажмите **Save** у workflow и переключите workflow в **Active**.

#### B. `Webhook Event`
1. Откройте ноду → **Parameters**.
2. Проверьте поля:
   - **HTTP Method**: `POST`
   - **Path**: `case/event/create`
   - **Authentication**: `None` (минимум для старта)
   - **Respond**: `Using 'Respond to Webhook' Node`
3. Для тестов используйте **Test URL** (`/webhook-test/case/event/create`).
4. Для продакшена используйте **Production URL** (`/webhook/case/event/create`).
5. Сохраните workflow и включите **Active**.

#### Важно про Test URL vs Production URL
- **Test URL** работает только когда вы нажали `Listen for test event` и обычно ограниченно по времени.
- **Production URL** работает постоянно (когда workflow активен).
- В вашем внешнем сервисе (CRM/форма/сайт) нужно вставлять именно **Production URL**.

#### Что отправлять в эти webhook (готовые примеры)
`POST /case/create`:
```json
{
  "case_code": "C-2026-001",
  "client_ref": "CLIENT-01",
  "lawyer_ref": "LAWYER-01",
  "case_type": "civil",
  "jurisdiction": "msk",
  "status": "new"
}
```

`POST /case/event/create`:
```json
{
  "case_code": "C-2026-001",
  "event_type": "court_hearing",
  "start_at": "2026-03-10T10:00:00+03:00",
  "end_at": "2026-03-10T10:30:00+03:00",
  "timezone": "Europe/Moscow",
  "lawyer_chat_id": "123456789"
}
```

#### Рекомендуемая защита (после запуска)
Когда убедитесь, что всё работает:
- добавьте секрет в заголовок (например `X-Webhook-Token`) через reverse proxy или отдельную проверку в начале потока;
- либо переключите `Authentication` с `None` на защищённый вариант (если используете его в вашей схеме).

---

### 4) Какие ноды ещё часто забывают донастроить
- `Webhook Case Create` и `Webhook Event`:
  - проверьте итоговые public URL вебхуков (домен n8n, reverse proxy, TLS).
- `REMIND ... Cron`:
  - проверьте интервал (сейчас 15 минут) и timezone инстанса n8n.
- Все Google Sheets ноды (`GS Read/Append ...`):
  - проверьте, что везде стоит один и тот же `GSHEET_ID` и credential `google_sheets_main`.

Быстрый smoke-test после настройки:
1. Создать дело через `/case/create`.
2. Отправить в Telegram фото или PDF с номером дела в подписи.
3. Создать событие через `/case/event/create`.
4. Убедиться, что напоминание появилось в `напоминания`, а после cron — в `журнал_отправки_напоминаний`.


## Важно
- Этот вариант дешевле, но хуже по управляемости, чем БД.
- Не используйте ФИО/детали дела в названиях файлов — только коды дел.
- Для 152‑ФЗ хранение клиентских ПДн в Google Sheets юридически рискованно; если есть ПДн, используйте РФ‑хранилище.

## Полное обновление локально + удалённо одним скриптом
Используйте `scripts_sync_and_bundle.ps1`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts_sync_and_bundle.ps1 -RepoPath "C:\Users\HP\Desktop\Vardkesovna" -RepoUrl "https://github.com/alexdmitrievi/Vardkesonva.git" -Branch main -PushToRemote
```

Что делает скрипт:
1. Синхронизирует локальный репозиторий с GitHub (`fetch`, `reset --hard`, `clean -fd`).
2. Собирает один файл `workflows/ALL_WORKFLOWS_BUNDLE.json` из отдельных `WF_*.json` (без повторного включения уже готового `WF_UNIFIED_LEGAL_AUTOMATION.json`).
3. При флаге `-PushToRemote` коммитит и пушит bundle в GitHub.

## Импорт одним файлом в n8n
В n8n: **Workflows → Import from File** и выберите файл:
- `workflows/WF_UNIFIED_LEGAL_AUTOMATION.json`

Текущая ревизия unified-файла в репозитории: `versionId = "2"` (обновлённая сборка).


## FAQ: Не слишком ли много нод в `WF_UNIFIED_LEGAL_AUTOMATION.json`?
Короткий ответ: **нет, это ожидаемо** для unified-варианта.

- В этом файле объединены **4 независимых сценария** (Case Create, Telegram Ingest, Event Create, Reminder Cron), поэтому граф визуально большой.
- Для текущей версии нормальный ориентир: около **48 nodes** и **43 connections**.
- В unified-файле есть **4 стартовых триггера** (`CASE`, `INGEST`, `EVENT`, `REMIND`) — это признак, что объединение собрано корректно.

Когда стоит разделять: 
- если команде тяжело сопровождать один большой граф;
- если нужно раздать права на отдельные процессы разным людям;
- если хотите упростить отладку и версионирование.

Практика для production: хранить оба формата — `WF_UNIFIED_*` (быстрый импорт одним файлом) и отдельные `WF_*.json` (удобная поддержка).


## Проверка соответствия вашим задачам
- ✅ Приём файлов в Telegram: поддержаны **фото**, **PDF**, **DOC/DOCX**, **TXT**.
- ✅ Привязка к делу: файл уходит в папку `01_Incoming` по `case_code`/номеру дела.
- ✅ Напоминания юристам: создаются при событии по делу (по умолчанию за 24ч и 2ч до процесса/дедлайна).
- ✅ Напоминания клиентам об оплате: создаются, если в `POST /case/event/create` переданы `client_chat_id` и `payment_due_at` (опционально `payment_amount`).
- ✅ Защита от повторной отправки напоминаний: cron исключает уже отправленные `id_напоминания` из `журнал_отправки_напоминаний`.

### Минимальный payload для напоминания клиенту об оплате
```json
{
  "case_code": "C-2026-001",
  "event_type": "payment_due",
  "start_at": "2026-03-10T10:00:00+03:00",
  "end_at": "2026-03-10T10:30:00+03:00",
  "timezone": "Europe/Moscow",
  "lawyer_chat_id": "123456789",
  "client_chat_id": "987654321",
  "payment_due_at": "2026-03-09T10:00:00+03:00",
  "payment_amount": "15000 RUB"
}
```

## Интеграция с Yandex Cloud (после создания VM)
Рекомендуемый production-путь под 152-ФЗ:
1. Оставить `n8n` и Nextcloud на вашей VM в Yandex Cloud.
2. Перенести метаданные дел из Google Sheets в **Managed Service for PostgreSQL** (или YDB), размещённый в РФ-регионе.
3. Поднять небольшой backend/API (например, FastAPI) на VM или в Serverless Containers, который пишет/читает метаданные в PostgreSQL.
4. В workflow включить зеркалирование в Yandex Cloud через env:
   - `YC_METADATA_MIRROR=1`
   - `YC_METADATA_API_URL=https://<ваш-api-домен>`
   - credential `yc_backend_api` (HTTP Header Auth, bearer token).

Что уже добавлено в workflow:
- условные узлы `IF YC Mirror Enabled`;
- HTTP-узлы `YC Mirror ...` для дел, документов, событий и лога отправленных напоминаний;
- если mirror выключен, workflow работает как раньше (через Google Sheets).

Это позволяет мигрировать поэтапно: сначала dual-write (Sheets + Yandex), затем полный переход на PostgreSQL.

## Нужно ли соединять 4 ветки между собой?
Коротко: **нет, в unified-файле это должны быть 4 отдельные ветки**.

Почему так:
- у каждой ветки свой триггер (`Webhook Case Create`, `Webhook Event`, `Cron`, `Telegram Trigger`);
- это 4 независимых бизнес-процесса, которые запускаются в разное время и разными источниками;
- если соединить их в одну цепочку, появятся ложные запуски и побочные эффекты (например, cron может случайно тащить ветку ingest).

Когда их можно связывать:
- только через **данные** (Google Sheets/PostgreSQL/API), а не прямым проводом node→node;
- либо через явный `Execute Workflow`/Webhook-вызов для осознанной оркестрации.

Рекомендация:
- в `WF_UNIFIED_LEGAL_AUTOMATION.json` держать 4 изолированные дорожки на одном canvas (как сейчас),
- для сопровождения в production хранить также отдельные `WF_*.json`.

## Про "красивые" связи и чтобы ноды не накладывались
Да, можно сделать **полуавтоматически** (не только вручную):
- при сборке unified-файла скрипт раскладывает каждый подпроцесс в отдельную "дорожку" (lane) по `Y`;
- позиции нод внутри каждого подпроцесса нормализуются и сдвигаются, чтобы блоки не наслаивались.

Что важно:
- n8n не гарантирует идеальный auto-layout для сложных графов;
- после импорта иногда всё равно полезен лёгкий ручной "косметический" тюнинг 2–3 узлов.

То есть базово — автоматом, финальный визуальный полиш — по желанию вручную.

## Как правильно скопировать файл из GitHub (кнопка с тремя точками)
Если открыли diff файла в GitHub и видите меню:
- `Скопировать применение git`
- `Скопировать патч`
- `Скопировать файл`

То для вставки **полного содержимого файла** (в локальный `.json` или при ручном редактировании файла в GitHub) нажимайте:

- ✅ **`Скопировать файл`**

Что делают другие пункты:
- `Скопировать патч` — копирует diff (изменения со знаками `+/-`), это не готовый JSON-файл.
- `Скопировать применение git` — копирует команду/инструкцию для применения изменений через git.

### В локальную папку (Windows)
1. Нажмите `Скопировать файл` в GitHub.
2. Откройте Блокнот/VS Code.
3. Вставьте (`Ctrl+V`).
4. Сохраните как `workflows/WF_UNIFIED_LEGAL_AUTOMATION.json` (UTF-8).

### Прямо в GitHub-файл
1. Откройте нужный файл в репозитории.
2. Нажмите `Edit` (иконка карандаша).
3. Выделите всё содержимое (`Ctrl+A`) и вставьте скопированное через `Скопировать файл` (`Ctrl+V`).
4. Commit changes.

Быстрая проверка, что вставился именно полный workflow (а не патч):

```powershell
$obj = Get-Content .\workflows\WF_UNIFIED_LEGAL_AUTOMATION.json -Raw | ConvertFrom-Json
"nodes=" + $obj.nodes.Count
"connections=" + ($obj.connections.PSObject.Properties).Count
```

Если `nodes` десятки и `connections` больше 10 — обычно файл вставлен корректно.

### Если в Cursor/PowerShell видите ошибку `git : Already on 'main'`
Это не критическая ошибка git, а особенность PowerShell при обработке stderr native-команд.
Обновите скрипт из репозитория до актуальной версии и запустите снова — в текущей версии это обработано.
