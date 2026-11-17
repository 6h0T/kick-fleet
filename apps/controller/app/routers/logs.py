from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import require_token
from app.models import EventLog
from app.redis_bus import bus
from app.schemas import LogIn

router = APIRouter(prefix="/api/v1/logs", tags=["logs"], dependencies=[Depends(require_token)])


@router.get("")
async def list_logs(limit: int = 300, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(EventLog).order_by(EventLog.created_at.desc()).limit(limit))).scalars().all()
    return [
        {
            "id": r.id,
            "worker_id": r.worker_id,
            "level": r.level,
            "message": r.message,
            "extra": r.extra,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.post("")
async def ingest(body: LogIn, db: AsyncSession = Depends(get_db)):
    row = EventLog(worker_id=body.worker_id, level=body.level, message=body.message, extra=body.extra)
    db.add(row)
    await db.commit()
    await bus.publish({"type": "log", **body.model_dump()})
    return {"ok": True}
