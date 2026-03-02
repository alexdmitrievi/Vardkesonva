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
3. Создайте credentials:
   - `nextcloud_webdav`
   - `telegram_main_bot`
   - `yandex_calendar_api`
   - `google_sheets_main`
4. В Google Sheets создайте листы:
   - `дела`
   - `папки_дел`
   - `документы`
   - `события_календаря`
   - `напоминания`
   - `журнал_отправки_напоминаний`
5. Замените плейсхолдеры URL (`nextcloud.example.ru`, endpoint календаря).

> Примечание: `ALL_WORKFLOWS_BUNDLE.json` — это массив workflow-объектов. В ряде версий n8n Cloud импорт из редактора может не отрисовать его как один workflow. Используйте `WF_UNIFIED_LEGAL_AUTOMATION.json` для надёжного импорта одним файлом.


### Для новичка: главный вопрос про Nextcloud (без воды)
- **Да, URL хоста можно брать из VM Yandex Cloud** — это ваш публичный IP/домен, по которому открывается Nextcloud.
- **Нет, app-password Nextcloud не берётся из VM** — его нужно создать в самом Nextcloud: `Аватар → Settings → Security → App passwords`.
- В credential `nextcloud_webdav` заполняете так:
  - `Username`: ваш логин Nextcloud;
  - `Password`: app-password из Nextcloud;
  - `Base URL/Host`: `https://<ваш_nextcloud_домен>` (или временно IP).

## Какие данные именно брать из виртуальной машины (Yandex Cloud)
Короткий ответ: **напрямую из строки VM в ноды почти ничего не вставляется**, кроме адресов ваших сервисов, которые крутятся на этой VM.

### Ответ на ваш вопрос в одном блоке (очень коротко)
- **URL хоста для Nextcloud**: берёте **не из n8n**, а из того адреса, по которому реально открывается ваш Nextcloud.
  - Если домен уже настроен: `https://nextcloud.<ваш-домен>`.
  - Если домена пока нет: временно можно `http://<Публичный_IP_VM>` (или `https://`, если уже настроен TLS).
- **App-password Nextcloud**: берёте **не из Yandex Cloud VM**, а создаёте в самом Nextcloud:
  - `Аватар (правый верх) → Settings (Личные настройки) → Security → Devices & sessions / App passwords → Create new app password`.
  - В n8n credential `nextcloud_webdav`: `Username = ваш Nextcloud пользователь`, `Password = этот app-password`.
- **Из VM Yandex Cloud** обычно берёте только:
  - публичный IP (или понимаете, какой домен указывает на VM),
  - SSH-доступ, чтобы администрировать сервер.

Итого: **IP/домен — да, может прийти из VM; app-password — только из интерфейса Nextcloud**.

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
   - IP VM в webhook-ноду вручную не втавляется, он уже входит в URL вашего n8n-домена/хоста.

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

### 3.1) Очень простая настройка по нода (для новичка, без кода)
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

## Шпаргалка «нода → строка → что вставить → откуда взять» (без лишних пояснений)

### Супер-формат (Node → Field → Value → Source) для самых частых ошибок

| Node | Field | Value | Source |
|---|---|---|---|
| `CASE_CREATE_AND_FOLDERS :: DAV MKCOL Incoming` | `URL` | `https://<NEXTCLOUD>/remote.php/dav/files/<USER>{{$json.incoming}}` | ваш Nextcloud домен/IP + username |
| `CASE_CREATE_AND_FOLDERS :: DAV MKCOL Outgoing` | `URL` | `https://<NEXTCLOUD>/remote.php/dav/files/<USER>{{$json.outgoing}}` | ваш Nextcloud домен/IP + username |
| `CASE_CREATE_AND_FOLDERS :: DAV MKCOL Evidence` | `URL` | `https://<NEXTCLOUD>/remote.php/dav/files/<USER>{{$json.evidence}}` | ваш Nextcloud домен/IP + username |
| `TELEGRAM_DOCUMENT_INGEST :: DAV Upload` | `URL` | `https://<NEXTCLOUD>/remote.php/dav/files/<USER>{{$json.folder_path}}/{{$json.stored_filename}}` | ваш Nextcloud домен/IP + username |
| `* DAV ...` (все Nextcloud HTTP ноды) | `Credential` | `nextcloud_webdav` | n8n Credentials |
| `* GS ...` | `Sheet ID` | `={{$env.GSHEET_ID}}` | `Settings → Variables` |
| `* GS ...` | `Credential` | `google_sheets_main` | n8n Credentials |
| `* Telegram ...` | `Credential` | `telegram_main_bot` | токен BotFather |
| `CASE_EVENT_CREATE :: Calendar Create` | `Credential` | `yandex_calendar_api` | ваш API token/header |

> Формат ниже сделан специально для новичка: открыл ноду → нашёл поле → вставил значение.

### Сначала заполните 4 credentials (один раз)
- `nextcloud_webdav`:
  - Host/Base URL: `https://<ваш-nextcloud-домен>` (или временно IP VM).
  - Username: `<пользователь nextcloud>`.
  - Password: `<app-password из Nextcloud Security>`.
- `google_sheets_main`: OAuth/Service Account с доступом на редактирование таблицы.
- `telegram_main_bot`: токен бота от BotFather.
- `yandex_calendar_api`: bearer token/API ключ вашего календарного API.

### Где именно брать URL и пароль Nextcloud
- URL: откройте Nextcloud в браузере. Всё до `/remote.php/...` — это ваш host URL.
  - пример: если в браузере `https://cloud.example.ru/apps/files/`, то host URL = `https://cloud.example.ru`.
- App-password: в самом Nextcloud (`Settings → Security → App passwords`).
- В Yandex Cloud VM **нет** поля, где лежит app-password Nextcloud.

### CASE_CREATE_AND_FOLDERS :: Webhook Case Create
- HTTP Method → `POST` → вручную (как указано).
- Path → `case/create` → вручную.
- Authentication → `None` → вручную (или ваш защищённый вариант).
- Respond → `Using 'Respond to Webhook' Node` → вручную.

### CASE_CREATE_AND_FOLDERS :: GS Read Cases
- Credential → `google_sheets_main` → из созданного credential Google Sheets.
- Sheet ID → `={{$env.GSHEET_ID}}` → из Variables (`GSHEET_ID` = ID таблицы из URL Google Sheets).
- Range → `дела!A:G` → вручную.

### CASE_CREATE_AND_FOLDERS :: DAV MKCOL Incoming
- URL → `https://<ВАШ_NEXTCLOUD>/remote.php/dav/files/<USER>{{$json.incoming}}` → домен/IP и USER из вашего Nextcloud.
- Method → `MKCOL` → вручную.
- Credential → `nextcloud_webdav` → из созданного credential Nextcloud.

### CASE_CREATE_AND_FOLDERS :: DAV MKCOL Outgoing
- URL → `https://<ВАШ_NEXTCLOUD>/remote.php/dav/files/<USER>{{$json.outgoing}}` → из Nextcloud.
- Method → `MKCOL` → вручную.
- Credential → `nextcloud_webdav` → из credential.

### CASE_CREATE_AND_FOLDERS :: DAV MKCOL Evidence
- URL → `https://<ВАШ_NEXTCLOUD>/remote.php/dav/files/<USER>{{$json.evidence}}` → из Nextcloud.
- Method → `MKCOL` → вручную.
- Credential → `nextcloud_webdav` → из credential.

### CASE_CREATE_AND_FOLDERS :: GS Append Case
- Credential → `google_sheets_main` → из credential.
- Sheet ID → `={{$env.GSHEET_ID}}` → из Variables.
- Range → `дела!A:G` → вручную.

### CASE_CREATE_AND_FOLDERS :: GS Append Folders
- Credential → `google_sheets_main` → из credential.
- Sheet ID → `={{$env.GSHEET_ID}}` → из Variables.
- Range → `папки_дел!A:E` → вручную.

### CASE_EVENT_CREATE :: Webhook Event
- HTTP Method → `POST` → вручную.
- Path → `case/event/create` → вручную.
- Authentication → `None` → вручную.
- Respond → `Using 'Respond to Webhook' Node` → вручную.

### CASE_EVENT_CREATE :: Calendar Create
- URL → ваш endpoint календаря (`https://...`) → из вашего Yandex Calendar/API gateway.
- Method → `POST` → вручную.
- Credential → `yandex_calendar_api` → из созданного credential (token/header).

### CASE_EVENT_CREATE :: GS Append Event
- Credential → `google_sheets_main` → из credential.
- Sheet ID → `={{$env.GSHEET_ID}}` → из Variables.
- Range → `события_календаря!A:G` → вручную.

### CASE_EVENT_CREATE :: GS Append Reminder 24h / 2h / Client Payment
- Credential → `google_sheets_main` → из credential.
- Sheet ID → `={{$env.GSHEET_ID}}` → из Variables.
- Range → `напоминания!A:H` → вручную.

### REMINDER_DISPATCH_CRON :: Cron
- Interval (minutes) → `15` → вручную (или ваш интервал).

### REMINDER_DISPATCH_CRON :: GS Read Reminders
- Credential → `google_sheets_main` → из credential.
- Sheet ID → `={{$env.GSHEET_ID}}` → из Variables.
- Range → `напоминания!A:H` → вручную.

### REMINDER_DISPATCH_CRON :: GS Read Sent Log
- Credential → `google_sheets_main` → из credential.
- Sheet ID → `={{$env.GSHEET_ID}}` → из Variables.
- Range → `журнал_отправки_напоминаний!A:D` → вручную.

### REMINDER_DISPATCH_CRON :: TG Send
- Credential → `telegram_main_bot` → из созданного Telegram credential (токен бота).

### REMINDER_DISPATCH_CRON :: GS Sent Log
- Credential → `google_sheets_main` → из credential.
- Sheet ID → `={{$env.GSHEET_ID}}` → из Variables.
- Range → `журнал_отправки_напоминаний!A:D` → вручную.

### TELEGRAM_DOCUMENT_INGEST :: Telegram Trigger
- Credential → `telegram_main_bot` → из Telegram credential.

### TELEGRAM_DOCUMENT_INGEST :: GS Read Folders
- Credential → `google_sheets_main` → из credential.
- Sheet ID → `={{$env.GSHEET_ID}}` → из Variables.
- Range → `папки_дел!A:E` → вручную.

### TELEGRAM_DOCUMENT_INGEST :: DAV Upload
- URL → `https://<ВАШ_NEXTCLOUD>/remote.php/dav/files/<USER>{{$json.folder_path}}/{{$json.stored_filename}}` → домен/IP и USER из Nextcloud.
- Method → `PUT` → вручную.
- Credential → `nextcloud_webdav` → из credential.

### TELEGRAM_DOCUMENT_INGEST :: GS Append Document
- Credential → `google_sheets_main` → из credential.
- Sheet ID → `={{$env.GSHEET_ID}}` → из Variables.
- Range → `документы!A:H` → вручную.

### TELEGRAM_DOCUMENT_INGEST :: TG Case Not Found / TG Ack
- Credential → `telegram_main_bot` → из Telegram credential.

### Ноды mirror (настраивать только если включили YC mirror)
- `... IF YC Mirror Enabled`:
  - Variable `YC_METADATA_MIRROR` → `1` → из Variables.
  - Variable `YC_METADATA_API_URL` → `https://<ваш-api>` → из URL вашего backend API.
- `... YC Mirror Case Upsert`
- `... YC Mirror Event Upsert`
- `... YC Mirror Document Upsert`
- `... YC Mirror Reminder Sent`
  - URL → `={{$env.YC_METADATA_API_URL + '/...'}}` → из Variables.
  - Credential → `yc_backend_api` → из созданного HTTP Header Auth credential.

## Какие ноды у нас относятся к Nextcloud (очень простыми словами)
Ниже все ноды, которые работают именно с Nextcloud (WebDAV).

### Что такое Nextcloud-ноды в этом проекте
Это ноды, где в URL есть ваш Nextcloud и путь вида:
- `/remote.php/dav/files/...`

Они делают 2 вещи:
1. создают папки дела;
2. загружают файл в папку дела.

---

### 1) Ноды создания папок (workflow `CASE_CREATE_AND_FOLDERS`)
Эти 3 ноды — Nextcloud:
1. `DAV MKCOL Incoming`
2. `DAV MKCOL Outgoing`
3. `DAV MKCOL Evidence`

Что они делают простыми словами:
- `Incoming` — создаёт папку для входящих документов.
- `Outgoing` — создаёт папку для исходящих документов.
- `Evidence` — создаёт папку для доказательств.

Как их настроить:
- откройте каждую ноду;
- в поле `URL` замените `nextcloud.example.ru` на ваш домен/IP Nextcloud;
- в `Credentials` выберите `nextcloud_webdav`.

---

### 2) Нода загрузки файла (workflow `TELEGRAM_DOCUMENT_INGEST`)
Эта нода — Nextcloud:
- `DAV Upload`

Что она делает:
- берёт файл, который пришёл из Telegram,
- кладёт его в папку дела в Nextcloud (`01_Incoming`).

Как настроить:
- в `URL` заменить `nextcloud.example.ru` на ваш Nextcloud;
- `Credentials` = `nextcloud_webdav`;
- остальное не менять.

---

### 3) В unified-файле как они называются
Если вы работаете в `WF_UNIFIED_LEGAL_AUTOMATION.json`, те же ноды будут с префиксом:
- `CASE_CREATE_AND_FOLDERS :: DAV MKCOL Incoming`
- `CASE_CREATE_AND_FOLDERS :: DAV MKCOL Outgoing`
- `CASE_CREATE_AND_FOLDERS :: DAV MKCOL Evidence`
- `TELEGRAM_DOCUMENT_INGEST :: DAV Upload`

---

### Что чаще всего ломает Nextcloud-ноды
1. Неправильный URL (забыли заменить `nextcloud.example.ru`).
2. Неверные логин/пароль в credential `nextcloud_webdav`.
3. У пользователя Nextcloud нет прав на создание папок/загрузку файлов.
4. Неправильный базовый путь WebDAV (`/remote.php/dav/files/<user>/...`).

---

### Быстрая проверка для новичка (1 минута)
1. Откройте `DAV MKCOL Incoming` → нажмите `Execute previous nodes`.
2. В Nextcloud проверьте: появилась ли папка `.../01_Incoming`.
3. Отправьте тестовый файл в Telegram с кодом дела.
4. Проверьте, что `DAV Upload` прошёл успешно и файл появился в папке дела.

Если эти шаги прошли — Nextcloud часть настроена правильно.

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
- `IF YC Mirror Enabled` / `YC Mirror Reminder Sent` — толко при mirror.

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
