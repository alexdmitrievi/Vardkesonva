from typing import Any, Dict
from urllib.parse import urljoin

import httpx

from app.config import Settings


class N8nClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def post_webhook(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = urljoin(self.settings.n8n_base_url.rstrip("/") + "/", path.lstrip("/"))
        timeout = httpx.Timeout(self.settings.n8n_timeout_seconds)

        async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
            response = await client.post(url, json=payload)

        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text}

        return {
            "upstream_status": response.status_code,
            "data": body,
        }
