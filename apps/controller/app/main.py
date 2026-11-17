import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, update

from app.db import SessionLocal, engine, get_db
from app.models import Task, Worker
from app.redis_bus import bus
from app.routers import accounts, chat, logs, scripts, tasks, workers
from app.ws import relay_loop, socket_session


async def reaper() -> None:
    while True:
        await asyncio.sleep(5)
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=20)
        async with SessionLocal() as db:
            await db.execute(
                update(Worker)
                .where(Worker.last_heartbeat_at.is_not(None), Worker.last_heartbeat_at < cutoff, Worker.status != "stopped")
                .values(status="stale")
            )
            due = (
                await db.execute(
                    select(Task).where(
                        Task.status == "queued",
                        Task.worker_id.is_not(None),
                        Task.run_at <= datetime.now(timezone.utc),
                    )
                )
            ).scalars().all()
            for task in due:
                await bus.enqueue(task.worker_id, {"task_id": str(task.id)})
            await db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await bus.connect()
    relay = asyncio.create_task(relay_loop())
    reap = asyncio.create_task(reaper())
    try:
        yield
    finally:
        relay.cancel()
        reap.cancel()
        await bus.close()
        await engine.dispose()


app = FastAPI(title="Kick Fleet Controller", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(workers.router)
app.include_router(accounts.router)
app.include_router(tasks.router)
app.include_router(chat.router)
app.include_router(scripts.router)
app.include_router(logs.router)


@app.get("/health")
async def health(db=Depends(get_db)):
    workers_rows = (await db.execute(select(Worker))).scalars().all()
    try:
        await bus.client.ping()
        redis_ok = True
    except Exception:
        redis_ok = False
    return {
        "ok": True,
        "workers": {w.id: w.status for w in workers_rows},
        "redis": redis_ok,
    }


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await socket_session(websocket)
