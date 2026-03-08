from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CaseCreateRequest(BaseModel):
    case_code: str = Field(min_length=1, max_length=128)
    case_type: str = Field(min_length=1, max_length=128)
    client_ref: str = Field(min_length=1, max_length=128)
    lawyer_ref: str = Field(min_length=1, max_length=128)
    jurisdiction: str = Field(min_length=1, max_length=128)
    status: str = Field(min_length=1, max_length=64)


class EventCreateRequest(BaseModel):
    case_code: str = Field(min_length=1, max_length=128)
    event_type: str = Field(min_length=1, max_length=128)
    start_at: datetime
    end_at: datetime
    lawyer_chat_id: str = Field(min_length=1, max_length=64)
    event_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    timezone: Optional[str] = None
    reminder_24h: Optional[bool] = True
    reminder_2h: Optional[bool] = True
    reminder_30m: Optional[bool] = False
    custom_reminder_minutes: Optional[int] = None


class AIConsultRequest(BaseModel):
    case_code: str = Field(min_length=1, max_length=128)
    jurisdiction: str = Field(min_length=1, max_length=128)
    document_text: str = Field(min_length=1)


class ProxyResponse(BaseModel):
    ok: bool = True
    upstream_status: int
    data: Any


class FileItem(BaseModel):
    id: str
    case_code: str
    name: str
    size: int
    content_type: str
    created_at: str
    preview_url: Optional[str] = None
    download_url: Optional[str] = None


class FilesListResponse(BaseModel):
    items: List[FileItem]


class UploadFileResult(BaseModel):
    filename: str
    reason: Optional[str] = None
    item: Optional[FileItem] = None


class UploadResponse(BaseModel):
    uploaded: List[UploadFileResult]
    failed: List[UploadFileResult]


class HealthResponse(BaseModel):
    status: str
    app: str
    env: str
    require_auth: bool


class FileIndexEntry(BaseModel):
    id: str
    case_code: str
    name: str
    stored_name: str
    size: int
    content_type: str
    created_at: str
    relative_path: str


class FilesIndex(BaseModel):
    files: List[FileIndexEntry] = Field(default_factory=list)


class ValidationErrorResponse(BaseModel):
    detail: List[Dict[str, Any]]
