from typing import Any

import httpx

from agent.settings import settings


def _headers() -> dict[str, str]:
    if settings.api_token:
        return {"Authorization": f"Bearer {settings.api_token}"}
    return {}


class Controller:
    def __init__(self) -> None:
        self.http = httpx.AsyncClient(base_url=settings.controller_url, headers=_headers(), timeout=30.0)

    async def heartbeat(self, payload: dict[str, Any]) -> None:
        await self.http.post("/api/v1/workers/heartbeat", json=payload)

    async def log(self, level: str, message: str, extra: dict | None = None) -> None:
        await self.http.post("/api/v1/logs", json={"worker_id": settings.worker_id, "level": level, "message": message, "extra": extra or {}})

    async def claim(self, task_id: str | None = None) -> dict[str, Any]:
        params = {"task_id": task_id} if task_id else None
        r = await self.http.post(f"/api/v1/tasks/claim/{settings.worker_id}", params=params)
        r.raise_for_status()
        return r.json()

    async def report(self, task_id: str, body: dict[str, Any]) -> None:
        r = await self.http.post(f"/api/v1/tasks/{task_id}/report", json=body)
        r.raise_for_status()

    async def ingest_chat(self, body: dict[str, Any]) -> None:
        await self.http.post("/api/v1/chat/ingest", json=body)

    async def close(self) -> None:
        await self.http.aclose()
