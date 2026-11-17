import base64
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import require_token
from app.models import Worker
from app.redis_bus import bus
from app.schemas import WorkerHeartbeat, WorkerOut
from app.services.docker_ctl import lifecycle

router = APIRouter(prefix="/api/v1/workers", tags=["workers"], dependencies=[Depends(require_token)])


def to_out(row: Worker) -> WorkerOut:
    return WorkerOut(
        id=row.id,
        name=row.name,
        status=row.status,
        cpu_percent=row.cpu_percent,
        ram_mb=row.ram_mb,
        ram_limit_mb=row.ram_limit_mb,
        novnc_url=row.novnc_url,
        last_heartbeat_at=row.last_heartbeat_at,
        labels=row.labels or {},
        has_snapshot=bool(row.snapshot_jpeg),
    )


@router.get("", response_model=list[WorkerOut])
async def list_workers(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Worker).order_by(Worker.id))).scalars().all()
    return [to_out(r) for r in rows]


@router.post("/heartbeat", response_model=WorkerOut)
async def heartbeat(body: WorkerHeartbeat, db: AsyncSession = Depends(get_db)):
    row = await db.get(Worker, body.id)
    if row is None:
        row = Worker(id=body.id, name=body.name)
        db.add(row)
    row.name = body.name
    row.status = body.status
    row.cpu_percent = body.cpu_percent
    row.ram_mb = body.ram_mb
    row.ram_limit_mb = body.ram_limit_mb
    row.novnc_url = body.novnc_url
    row.vnc_port = body.vnc_port
    row.labels = body.labels
    row.last_heartbeat_at = datetime.now(timezone.utc)
    if body.snapshot_jpeg_b64:
        row.snapshot_jpeg = base64.b64decode(body.snapshot_jpeg_b64)
    await db.commit()
    await db.refresh(row)
    await bus.publish(
        {
            "type": "worker",
            "id": row.id,
            "status": row.status,
            "cpu_percent": row.cpu_percent,
            "ram_mb": row.ram_mb,
        }
    )
    return to_out(row)


@router.get("/{worker_id}", response_model=WorkerOut)
async def get_worker(worker_id: str, db: AsyncSession = Depends(get_db)):
    row = await db.get(Worker, worker_id)
    if not row:
        raise HTTPException(404, "worker not found")
    return to_out(row)


@router.get("/{worker_id}/snapshot")
async def snapshot(worker_id: str, db: AsyncSession = Depends(get_db)):
    row = await db.get(Worker, worker_id)
    if not row or not row.snapshot_jpeg:
        raise HTTPException(404, "no snapshot")
    return Response(content=row.snapshot_jpeg, media_type="image/jpeg")


@router.post("/{worker_id}/{action}")
async def control(worker_id: str, action: str, db: AsyncSession = Depends(get_db)):
    if action not in {"start", "stop", "restart"}:
        raise HTTPException(400, "action must be start, stop, or restart")
    try:
        result = lifecycle(worker_id, action)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
    row = await db.get(Worker, worker_id)
    if row:
        row.status = "starting" if action in {"start", "restart"} else "stopped"
        await db.commit()
    await bus.publish({"type": "worker-control", "worker_id": worker_id, "action": action, "result": result})
    return result
