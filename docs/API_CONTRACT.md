# API Contract (Backend -> n8n + files)

Base URL (default local): `http://localhost:8000`  
API prefix: `/api/v1`

If `REQUIRE_AUTH=true`, include header:

```
Authorization: Bearer <API_BEARER_TOKEN>
```

## Health

### `GET /healthz`

Response:

```json
{
  "status": "ok",
  "app": "legal-automation-backend",
  "env": "development",
  "require_auth": false
}
```

## Case creation

### `POST /api/v1/cases/create`

Request:

```json
{
  "case_code": "A40-12345/2026",
  "case_type": "arbitration_debt",
  "client_ref": "client_001",
  "lawyer_ref": "lawyer_007",
  "jurisdiction": "Россия",
  "status": "new"
}
```

Backend proxy target (fixed path):  
`POST <N8N_BASE_URL>/webhook/case/create`

Response:

```json
{
  "ok": true,
  "upstream_status": 200,
  "data": {
    "result": "accepted"
  }
}
```

## Event creation

### `POST /api/v1/events/create`

Request:

```json
{
  "case_code": "A40-12345/2026",
  "event_type": "court_hearing",
  "start_at": "2026-03-20T07:00:00.000Z",
  "end_at": "2026-03-20T08:00:00.000Z",
  "lawyer_chat_id": "123456789"
}
```

Backend proxy target (fixed path):  
`POST <N8N_BASE_URL>/webhook/case/event/create`

Response shape:

```json
{
  "ok": true,
  "upstream_status": 200,
  "data": {}
}
```

## AI legal consult

### `POST /api/v1/ai/consult`

Request:

```json
{
  "case_code": "A40-12345/2026",
  "jurisdiction": "Россия",
  "document_text": "..."
}
```

Backend proxy target (fixed path):  
`POST <N8N_BASE_URL>/webhook/ai/legal/consult`

Response shape:

```json
{
  "ok": true,
  "upstream_status": 200,
  "data": {}
}
```

## Files list

### `GET /api/v1/files?case_code=A40-12345/2026`

Response:

```json
{
  "items": [
    {
      "id": "doc_001",
      "case_code": "A40-12345/2026",
      "name": "contract.pdf",
      "size": 245760,
      "content_type": "application/pdf",
      "created_at": "2026-03-08T16:11:00.000000+00:00",
      "preview_url": "http://localhost:8000/api/v1/files/doc_001/preview",
      "download_url": "http://localhost:8000/api/v1/files/doc_001/download"
    }
  ]
}
```

## Files upload

### `POST /api/v1/files/upload` (multipart/form-data)

Body:
- `case_code` (text)
- `files` (one or many files)

Allowed extensions: `jpg,jpeg,png,pdf,doc,docx,txt`.

Response:

```json
{
  "uploaded": [
    {
      "filename": "contract.pdf",
      "reason": null,
      "item": {
        "id": "doc_abc123",
        "case_code": "A40-12345/2026",
        "name": "contract.pdf",
        "size": 245760,
        "content_type": "application/pdf",
        "created_at": "2026-03-08T16:11:00.000000+00:00",
        "preview_url": "http://localhost:8000/api/v1/files/doc_abc123/preview",
        "download_url": "http://localhost:8000/api/v1/files/doc_abc123/download"
      }
    }
  ],
  "failed": []
}
```

## File preview

### `GET /api/v1/files/{id}/preview`

Returns file inline with original content type when available.

## File download

### `GET /api/v1/files/{id}/download`

Returns file as downloadable binary stream.

---

## Smoke curls

Use these commands after backend start.

### 1) Health

```bash
curl -i http://localhost:8000/healthz
```

### 2) Create case

```bash
curl -i -X POST http://localhost:8000/api/v1/cases/create \
  -H "Content-Type: application/json" \
  -d '{
    "case_code":"A40-12345/2026",
    "case_type":"arbitration_debt",
    "client_ref":"client_001",
    "lawyer_ref":"lawyer_007",
    "jurisdiction":"Россия",
    "status":"new"
  }'
```

### 3) Create event

```bash
curl -i -X POST http://localhost:8000/api/v1/events/create \
  -H "Content-Type: application/json" \
  -d '{
    "case_code":"A40-12345/2026",
    "event_type":"court_hearing",
    "start_at":"2026-03-20T07:00:00.000Z",
    "end_at":"2026-03-20T08:00:00.000Z",
    "lawyer_chat_id":"123456789"
  }'
```

### 4) AI consult

```bash
curl -i -X POST http://localhost:8000/api/v1/ai/consult \
  -H "Content-Type: application/json" \
  -d '{
    "case_code":"A40-12345/2026",
    "jurisdiction":"Россия",
    "document_text":"Проверь риски договора поставки."
  }'
```

### 5) Upload file

```bash
curl -i -X POST http://localhost:8000/api/v1/files/upload \
  -F "case_code=A40-12345/2026" \
  -F "files=@./sample.pdf"
```

### 6) List files

```bash
curl -i "http://localhost:8000/api/v1/files?case_code=A40-12345/2026"
```

### 7) Lint backend (ruff)

```bash
python -m ruff check backend/app backend/tests
```
