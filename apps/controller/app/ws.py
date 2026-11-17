import asyncio
import json
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from app.redis_bus import CHANNEL, bus

clients: set[WebSocket] = set()


async def register(ws: WebSocket) -> None:
    await ws.accept()
    clients.add(ws)


def unregister(ws: WebSocket) -> None:
    clients.discard(ws)


async def broadcast(event: dict[str, Any]) -> None:
    dead: list[WebSocket] = []
    payload = json.dumps(event, default=str)
    for ws in list(clients):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        unregister(ws)


async def relay_loop() -> None:
    assert bus.client is not None
    pubsub = bus.client.pubsub()
    await pubsub.subscribe(CHANNEL)
    try:
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg.get("data"):
                raw = msg["data"]
                if isinstance(raw, bytes):
                    event = json.loads(raw)
                else:
                    event = json.loads(raw)
                await broadcast(event)
            await asyncio.sleep(0.05)
    finally:
        await pubsub.unsubscribe(CHANNEL)


async def socket_session(ws: WebSocket) -> None:
    await register(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        unregister(ws)
    except Exception:
        unregister(ws)
