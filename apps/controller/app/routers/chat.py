from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import require_token
from app.models import Account, ChatMessage, InteractionScript
from app.redis_bus import bus
from app.schemas import ChatDispatch, ChatIn
from app.services.tasks import enqueue_task, substitute
from app.schemas import TaskCreate

router = APIRouter(prefix="/api/v1/chat", tags=["chat"], dependencies=[Depends(require_token)])


@router.get("/messages")
async def messages(limit: int = 200, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(ChatMessage).order_by(ChatMessage.created_at.desc()).limit(limit))).scalars().all()
    return [
        {
            "id": str(r.id),
            "account_id": str(r.account_id) if r.account_id else None,
            "worker_id": r.worker_id,
            "channel": r.channel,
            "direction": r.direction,
            "body": r.body,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.post("/ingest")
async def ingest(body: ChatIn, db: AsyncSession = Depends(get_db)):
    row = ChatMessage(
        account_id=body.account_id,
        worker_id=body.worker_id,
        channel=body.channel,
        direction=body.direction,
        body=body.body,
    )
    db.add(row)
    await db.commit()
    await bus.publish({"type": "chat", **body.model_dump(mode="json")})

    if body.direction == "in" and body.worker_id:
        # the auto-reply runs on the same worker the message came from
        scripts = (await db.execute(select(InteractionScript).where(InteractionScript.enabled.is_(True)))).scalars().all()
        for script in scripts:
            trigger = script.trigger or {}
            pattern = (trigger.get("contains") or "").lower()
            if pattern and pattern in body.body.lower():
                await enqueue_task(
                    db,
                    TaskCreate(
                        type="run_script",
                        worker_id=body.worker_id,
                        account_id=body.account_id,
                        payload={
                            "steps": substitute(script.steps, {"channel": body.channel, "text": trigger.get("reply", "")}),
                            "channel": body.channel,
                        },
                    ),
                )
    return {"ok": True}


@router.post("/dispatch")
async def dispatch(body: ChatDispatch, db: AsyncSession = Depends(get_db)):
    query = select(Account).where(Account.status.in_(["active", "session_live", "provisioning"]))
    if body.account_ids:
        query = query.where(Account.id.in_(body.account_ids))
    accounts = (await db.execute(query)).scalars().all()
    if not accounts:
        raise HTTPException(400, "no eligible accounts")

    script_steps = None
    if body.script_name:
        script = (await db.execute(select(InteractionScript).where(InteractionScript.name == body.script_name))).scalar_one_or_none()
        if not script:
            raise HTTPException(404, "script not found")
        script_steps = script.steps

    queued = []
    for account in accounts:
        worker_id = account.assigned_worker_id
        if body.worker_ids:
            worker_id = body.worker_ids[len(queued) % len(body.worker_ids)]
        if not worker_id:
            continue
        if script_steps is not None:
            task = await enqueue_task(
                db,
                TaskCreate(
                    type="run_script",
                    worker_id=worker_id,
                    account_id=account.id,
                    payload={"steps": substitute(script_steps, {"channel": body.channel, "text": body.text}), "channel": body.channel},
                ),
            )
        else:
            task = await enqueue_task(
                db,
                TaskCreate(
                    type="send_message",
                    worker_id=worker_id,
                    account_id=account.id,
                    payload={"channel": body.channel, "text": body.text},
                ),
            )
        queued.append(str(task.id))
    if not queued:
        raise HTTPException(400, "accounts have no assigned workers")
    return {"queued": queued}
