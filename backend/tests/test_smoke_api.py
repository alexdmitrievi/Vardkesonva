from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app, get_files_service, get_n8n_client
from app.services.files_service import FilesService


class DummyN8NClient:
    async def post_webhook(self, path, payload):
        return {"upstream_status": 200, "data": {"echo": payload, "path": path}}


def test_smoke_core_api(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("REQUIRE_AUTH", "false")
    get_settings.cache_clear()
    settings = Settings(storage_root=str(tmp_path), index_file_name="index.json")
    files_service = FilesService(settings)

    app.dependency_overrides[get_n8n_client] = lambda: DummyN8NClient()
    app.dependency_overrides[get_files_service] = lambda: files_service

    with TestClient(app) as client:
        case_payload = {
            "case_code": "A40-12345/2026",
            "case_type": "arbitration_debt",
            "client_ref": "client_001",
            "lawyer_ref": "lawyer_007",
            "jurisdiction": "Россия",
            "status": "new",
        }
        event_payload = {
            "case_code": "A40-12345/2026",
            "event_type": "court_hearing",
            "start_at": "2026-03-20T07:00:00.000Z",
            "end_at": "2026-03-20T08:00:00.000Z",
            "lawyer_chat_id": "123456789",
        }
        ai_payload = {
            "case_code": "A40-12345/2026",
            "jurisdiction": "Россия",
            "document_text": "Документ для проверки",
        }

        assert client.post("/api/v1/cases/create", json=case_payload).status_code == 200
        assert client.post("/api/v1/events/create", json=event_payload).status_code == 200
        assert client.post("/api/v1/ai/consult", json=ai_payload).status_code == 200

        upload = client.post(
            "/api/v1/files/upload",
            data={"case_code": "A40-12345/2026"},
            files={"files": ("contract.txt", b"contract body", "text/plain")},
        )
        assert upload.status_code == 200
        body = upload.json()
        assert len(body["uploaded"]) == 1
        file_id = body["uploaded"][0]["item"]["id"]

        listed = client.get("/api/v1/files", params={"case_code": "A40-12345/2026"})
        assert listed.status_code == 200
        assert listed.json()["items"]

        preview = client.get(f"/api/v1/files/{file_id}/preview")
        assert preview.status_code == 200
        assert preview.content == b"contract body"

        download = client.get(f"/api/v1/files/{file_id}/download")
        assert download.status_code == 200
        assert download.content == b"contract body"

    app.dependency_overrides.clear()
