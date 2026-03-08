from typing import List

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.schemas import (
    AIConsultRequest,
    CaseCreateRequest,
    EventCreateRequest,
    FilesListResponse,
    HealthResponse,
    ProxyResponse,
    UploadResponse,
)
from app.services.files_service import FilesService
from app.services.n8n_client import N8nClient


def get_n8n_client(settings: Settings = Depends(get_settings)) -> N8nClient:
    return N8nClient(settings)


def get_files_service(settings: Settings = Depends(get_settings)) -> FilesService:
    return FilesService(settings)


app = FastAPI(title="Legal Automation Backend API", version="1.0.0")


@app.middleware("http")
async def bearer_auth_middleware(request: Request, call_next):
    settings = get_settings()
    if settings.require_auth and request.url.path.startswith(settings.api_prefix):
        auth_header = request.headers.get("Authorization", "")
        expected = f"Bearer {settings.api_bearer_token}".strip()
        if not settings.api_bearer_token or auth_header != expected:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Unauthorized. Provide valid Bearer token."},
            )
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", response_model=HealthResponse)
def healthz(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        env=settings.app_env,
        require_auth=settings.require_auth,
    )


@app.post("/api/v1/cases/create", response_model=ProxyResponse)
async def create_case(
    payload: CaseCreateRequest,
    n8n_client: N8nClient = Depends(get_n8n_client),
    settings: Settings = Depends(get_settings),
) -> ProxyResponse:
    result = await n8n_client.post_webhook(settings.n8n_case_create_path, payload.model_dump())
    return ProxyResponse(ok=result["upstream_status"] < 400, **result)


@app.post("/api/v1/events/create", response_model=ProxyResponse)
async def create_event(
    payload: EventCreateRequest,
    n8n_client: N8nClient = Depends(get_n8n_client),
    settings: Settings = Depends(get_settings),
) -> ProxyResponse:
    result = await n8n_client.post_webhook(
        settings.n8n_event_create_path, payload.model_dump(mode="json")
    )
    return ProxyResponse(ok=result["upstream_status"] < 400, **result)


@app.post("/api/v1/ai/consult", response_model=ProxyResponse)
async def consult_ai(
    payload: AIConsultRequest,
    n8n_client: N8nClient = Depends(get_n8n_client),
    settings: Settings = Depends(get_settings),
) -> ProxyResponse:
    result = await n8n_client.post_webhook(settings.n8n_ai_consult_path, payload.model_dump())
    return ProxyResponse(ok=result["upstream_status"] < 400, **result)


@app.get("/api/v1/files", response_model=FilesListResponse)
def list_files(
    request: Request,
    case_code: str = Query(..., min_length=1),
    files_service: FilesService = Depends(get_files_service),
) -> FilesListResponse:
    base_url = str(request.base_url).rstrip("/")
    items = files_service.list_files(case_code=case_code, base_url=base_url)
    return FilesListResponse(items=items)


@app.post("/api/v1/files/upload", response_model=UploadResponse)
async def upload_files(
    request: Request,
    case_code: str = Form(..., min_length=1),
    files: List[UploadFile] = File(...),
    files_service: FilesService = Depends(get_files_service),
) -> UploadResponse:
    base_url = str(request.base_url).rstrip("/")
    uploaded, failed = await files_service.save_uploads(case_code, files, base_url=base_url)
    return UploadResponse(uploaded=uploaded, failed=failed)


@app.get("/api/v1/files/{file_id}/preview")
def preview_file(file_id: str, files_service: FilesService = Depends(get_files_service)) -> FileResponse:
    entry = files_service.get_file_entry(file_id)
    if not entry:
        raise HTTPException(status_code=404, detail="File not found")
    path = files_service.resolve_file_path(entry)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File is missing in storage")
    return FileResponse(path=str(path), media_type=entry.content_type, filename=entry.name)


@app.get("/api/v1/files/{file_id}/download")
def download_file(
    file_id: str, files_service: FilesService = Depends(get_files_service)
) -> FileResponse:
    entry = files_service.get_file_entry(file_id)
    if not entry:
        raise HTTPException(status_code=404, detail="File not found")
    path = files_service.resolve_file_path(entry)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File is missing in storage")
    return FileResponse(
        path=str(path),
        media_type="application/octet-stream",
        filename=entry.name,
    )
