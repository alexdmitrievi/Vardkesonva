import json
import re
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import List, Optional, Tuple
from uuid import uuid4

from fastapi import UploadFile

from app.config import Settings
from app.schemas import FileIndexEntry, FileItem, FilesIndex, UploadFileResult


def _sanitize_case_code(case_code: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", case_code.strip())
    return cleaned or "unknown_case"


def _sanitize_filename(filename: str) -> str:
    base_name = Path(filename).name
    stem = re.sub(r"[^a-zA-Z0-9._-]+", "_", Path(base_name).stem).strip("._")
    suffix = re.sub(r"[^a-zA-Z0-9.]+", "", Path(base_name).suffix.lower())
    safe_stem = stem or "file"
    return f"{safe_stem}{suffix}"


class FilesService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = Lock()
        self._init_storage()

    def _init_storage(self) -> None:
        self.settings.storage_path.mkdir(parents=True, exist_ok=True)
        if not self.settings.index_path.exists():
            with self.settings.index_path.open("w", encoding="utf-8") as fp:
                json.dump({"files": []}, fp, ensure_ascii=True, indent=2)

    def _read_index(self) -> FilesIndex:
        with self._lock:
            with self.settings.index_path.open("r", encoding="utf-8") as fp:
                payload = json.load(fp)
        return FilesIndex.model_validate(payload)

    def _write_index(self, index: FilesIndex) -> None:
        tmp_path = self.settings.index_path.with_suffix(".tmp")
        with self._lock:
            with tmp_path.open("w", encoding="utf-8") as fp:
                json.dump(index.model_dump(), fp, ensure_ascii=True, indent=2)
            tmp_path.replace(self.settings.index_path)

    def _build_urls(self, item: FileItem, base_url: str) -> FileItem:
        item.preview_url = f"{base_url}/api/v1/files/{item.id}/preview"
        item.download_url = f"{base_url}/api/v1/files/{item.id}/download"
        return item

    def _entry_to_item(self, entry: FileIndexEntry, base_url: Optional[str] = None) -> FileItem:
        item = FileItem(
            id=entry.id,
            case_code=entry.case_code,
            name=entry.name,
            size=entry.size,
            content_type=entry.content_type,
            created_at=entry.created_at,
        )
        if base_url:
            return self._build_urls(item, base_url.rstrip("/"))
        return item

    def list_files(self, case_code: str, base_url: Optional[str] = None) -> List[FileItem]:
        index = self._read_index()
        items = [
            self._entry_to_item(entry, base_url=base_url)
            for entry in index.files
            if entry.case_code == case_code
        ]
        items.sort(key=lambda i: i.created_at, reverse=True)
        return items

    def _is_allowed_extension(self, filename: str) -> bool:
        ext = Path(filename).suffix.lower().lstrip(".")
        return ext in self.settings.allowed_file_extensions

    async def save_uploads(
        self, case_code: str, files: List[UploadFile], base_url: Optional[str] = None
    ) -> Tuple[List[UploadFileResult], List[UploadFileResult]]:
        if not case_code.strip():
            return [], [UploadFileResult(filename="", reason="case_code is required")]

        safe_case_code = _sanitize_case_code(case_code)
        case_dir = self.settings.storage_path / safe_case_code
        case_dir.mkdir(parents=True, exist_ok=True)

        uploaded: List[UploadFileResult] = []
        failed: List[UploadFileResult] = []

        index = self._read_index()

        for upload in files:
            safe_name = _sanitize_filename(upload.filename or "file")
            if not self._is_allowed_extension(safe_name):
                failed.append(
                    UploadFileResult(
                        filename=upload.filename or safe_name,
                        reason="unsupported extension",
                    )
                )
                continue

            content = await upload.read()
            size_bytes = len(content)
            if size_bytes > self.settings.max_upload_size_mb * 1024 * 1024:
                failed.append(
                    UploadFileResult(
                        filename=upload.filename or safe_name,
                        reason=f"file too large, max {self.settings.max_upload_size_mb} MB",
                    )
                )
                continue

            file_id = f"doc_{uuid4().hex[:12]}"
            stored_name = f"{file_id}_{safe_name}"
            target_path = case_dir / stored_name
            target_path.write_bytes(content)

            entry = FileIndexEntry(
                id=file_id,
                case_code=case_code,
                name=safe_name,
                stored_name=stored_name,
                size=size_bytes,
                content_type=upload.content_type or "application/octet-stream",
                created_at=datetime.now(timezone.utc).isoformat(),
                relative_path=str(target_path.relative_to(self.settings.storage_path)),
            )
            index.files.append(entry)
            item = self._entry_to_item(entry, base_url=base_url)
            uploaded.append(UploadFileResult(filename=safe_name, item=item))

        self._write_index(index)
        return uploaded, failed

    def get_file_entry(self, file_id: str) -> Optional[FileIndexEntry]:
        index = self._read_index()
        for entry in index.files:
            if entry.id == file_id:
                return entry
        return None

    def resolve_file_path(self, entry: FileIndexEntry) -> Path:
        return self.settings.storage_path / entry.relative_path
