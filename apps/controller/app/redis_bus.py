import json
from typing import Any

import redis.asyncio as redis

from app.config import settings

CHANNEL = "fleet.events"
TASK_QUEUE = "fleet.tasks"


class Bus:
    def __init__(self) -> None:
        self.client: redis.Redis | None = None

    async def connect(self) -> None:
        self.client = redis.from_url(settings.redis_url, decode_responses=False)
        await self.client.ping()

    async def close(self) -> None:
        if self.client:
            await self.client.close()

    def _r(self) -> redis.Redis:
        if not self.client:
            raise RuntimeError("redis not connected")
        return self.client

    async def publish(self, event: dict[str, Any]) -> None:
        await self._r().publish(CHANNEL, json.dumps(event, default=str).encode())

    async def enqueue(self, worker_id: str, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, default=str).encode()
        await self._r().lpush(f"{TASK_QUEUE}:{worker_id}", data)

    async def dequeue(self, worker_id: str, timeout: int = 5) -> dict[str, Any] | None:
        item = await self._r().brpop(f"{TASK_QUEUE}:{worker_id}", timeout=timeout)
        if not item:
            return None
        _, raw = item
        return json.loads(raw)


bus = Bus()
