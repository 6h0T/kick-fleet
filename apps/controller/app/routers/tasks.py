import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import require_token
from app.models import Task
from app.schemas import TaskClaimOut, TaskCreate, TaskOut, TaskReport
from app.services.tasks import claim_task, enqueue_task, finish_task

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"], dependencies=[Depends(require_token)])


@router.get("", response_model=list[TaskOut])
async def list_tasks(limit: int = 100, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Task).order_by(Task.created_at.desc()).limit(limit))).scalars().all()
    return rows


@router.post("", response_model=TaskOut)
async def create_task(body: TaskCreate, db: AsyncSession = Depends(get_db)):
    return await enqueue_task(db, body)


@router.post("/claim/{worker_id}", response_model=TaskClaimOut)
async def claim(worker_id: str, task_id: uuid.UUID | None = None, db: AsyncSession = Depends(get_db)):
    task, creds, storage = await claim_task(db, worker_id, task_id)
    if not task:
        return TaskClaimOut()
    return TaskClaimOut(task=TaskOut.model_validate(task), credentials=creds, storage_state=storage)


@router.post("/{task_id}/report", response_model=TaskOut)
async def report(task_id: uuid.UUID, body: TaskReport, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "task not found")
    return await finish_task(db, task, body.status, body.result, body.error, body.storage_state, body.account_status, body.health_delta)


@router.get("/due")
async def due(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    rows = (
        await db.execute(
            select(Task).where(Task.status == "queued", Task.run_at <= now, Task.worker_id.is_not(None))
        )
    ).scalars().all()
    return [{"id": str(t.id), "worker_id": t.worker_id} for t in rows]
