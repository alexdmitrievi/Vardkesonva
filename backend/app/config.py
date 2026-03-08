from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "legal-automation-backend"
    app_env: str = "development"
    api_prefix: str = "/api/v1"

    n8n_base_url: str = "http://localhost:5678"
    n8n_timeout_seconds: float = 30.0
    n8n_case_create_path: str = "/webhook/case/create"
    n8n_event_create_path: str = "/webhook/case/event/create"
    n8n_ai_consult_path: str = "/webhook/ai/legal/consult"

    require_auth: bool = False
    api_bearer_token: str = ""
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:8080"])

    max_upload_size_mb: int = 25
    allowed_file_extensions: List[str] = Field(
        default_factory=lambda: ["jpg", "jpeg", "png", "pdf", "doc", "docx", "txt"]
    )
    storage_root: str = "storage"
    index_file_name: str = "index.json"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> List[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return []

    @field_validator("allowed_file_extensions", mode="before")
    @classmethod
    def parse_extensions(cls, value: object) -> List[str]:
        if isinstance(value, list):
            return [str(item).lower().strip().lstrip(".") for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.lower().strip().lstrip(".") for item in value.split(",") if item.strip()]
        return ["jpg", "jpeg", "png", "pdf", "doc", "docx", "txt"]

    @property
    def storage_path(self) -> Path:
        project_root = Path(__file__).resolve().parents[1]
        path = Path(self.storage_root)
        if not path.is_absolute():
            path = project_root / path
        return path

    @property
    def index_path(self) -> Path:
        return self.storage_path / self.index_file_name


@lru_cache
def get_settings() -> Settings:
    return Settings()
