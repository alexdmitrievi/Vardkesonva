from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_healthz_ok(monkeypatch):
    monkeypatch.setenv("REQUIRE_AUTH", "false")
    get_settings.cache_clear()

    client = TestClient(app)
    response = client.get("/healthz")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "legal-automation-backend"


def test_auth_middleware(monkeypatch):
    monkeypatch.setenv("REQUIRE_AUTH", "true")
    monkeypatch.setenv("API_BEARER_TOKEN", "secret-token")
    get_settings.cache_clear()

    client = TestClient(app)

    unauthorized = client.get("/api/v1/files", params={"case_code": "A40-12345/2026"})
    assert unauthorized.status_code == 401

    authorized = client.get(
        "/api/v1/files",
        params={"case_code": "A40-12345/2026"},
        headers={"Authorization": "Bearer secret-token"},
    )
    assert authorized.status_code == 200
