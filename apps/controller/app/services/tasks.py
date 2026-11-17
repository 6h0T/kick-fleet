import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crypto import decrypt_json, encrypt_json
from app.models import Account, SessionRow, Task
from app.redis_bus import bus
from app.schemas import TaskCreate


async def enqueue_task(db: AsyncSession, body: TaskCreate) -> Task:
    run_at = body.run_at or datetime.now(timezone.utc)
    if run_at.tzinfo is None:  # clients may send naive datetimes; treat as UTC
        run_at = run_at.replace(tzinfo=timezone.utc)
    task = Task(
        type=body.type,
        worker_id=body.worker_id,
        account_id=body.account_id,
        payload=body.payload,
        run_at=run_at,
        status="queued",
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    if task.worker_id and task.run_at <= datetime.now(timezone.utc):
        await bus.enqueue(task.worker_id, {"task_id": str(task.id)})
        await bus.publish({"type": "task", "task_id": str(task.id), "status": "queued", "worker_id": task.worker_id})
    return task


async def claim_task(db: AsyncSession, worker_id: str, task_id: uuid.UUID | None = None) -> tuple[Task | None, dict | None, dict | None]:
    task: Task | None = None
    if task_id:
        task = await db.get(Task, task_id)
        if task and task.status != "queued":
            task = None
    if task is None:
        queued = await db.execute(
            select(Task)
            .where(Task.status == "queued", Task.worker_id == worker_id, Task.run_at <= datetime.now(timezone.utc))
            .order_by(Task.run_at)
            .limit(1)
        )
        task = queued.scalar_one_or_none()
    if task is None:
        return None, None, None
    task.status = "running"
    task.started_at = datetime.now(timezone.utc)
    creds = None
    storage = None
    if task.account_id:
        account = await db.get(Account, task.account_id)
        if account:
            creds = decrypt_json(account.credential_blob)
            creds["username"] = account.username
            creds["platform"] = account.platform
            sess = await db.execute(
                select(SessionRow)
                .where(SessionRow.account_id == account.id, SessionRow.storage_state_blob.is_not(None))
                .order_by(SessionRow.last_seen_at.desc())
                .limit(1)
            )
            row = sess.scalar_one_or_none()
            if row and row.storage_state_blob:
                storage = decrypt_json(row.storage_state_blob)
    await db.commit()
    await db.refresh(task)
    return task, creds, storage


async def finish_task(db: AsyncSession, task: Task, status: str, result: dict | None, error: str | None, storage_state: dict | None, account_status: str | None, health_delta: int | None) -> Task:
    task.status = status
    task.result = result
    task.error = error
    task.finished_at = datetime.now(timezone.utc)
    if task.account_id:
        account = await db.get(Account, task.account_id)
        if account:
            if account_status:
                account.status = account_status
            if health_delta:
                account.health_score = max(0, min(100, account.health_score + health_delta))
            if status == "done" and task.type in {"login", "open_channel", "send_message", "run_script"}:
                account.last_login_at = datetime.now(timezone.utc)
            if storage_state is not None:
                blob = encrypt_json(storage_state)
                sess = SessionRow(
                    account_id=account.id,
                    worker_id=task.worker_id,
                    status="live" if status == "done" else "error",
                    storage_state_blob=blob,
                )
                db.add(sess)
            account.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(task)
    await bus.publish({"type": "task", "task_id": str(task.id), "status": task.status, "worker_id": task.worker_id, "error": error})
    return task


def substitute(steps: list, mapping: dict) -> list:
    raw = json.dumps(steps)
    for key, value in mapping.items():
        raw = raw.replace("{{" + key + "}}", str(value))
    return json.loads(raw)
