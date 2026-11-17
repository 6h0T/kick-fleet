from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import require_token
from app.models import InteractionScript
from app.schemas import ScriptIn

router = APIRouter(prefix="/api/v1/scripts", tags=["scripts"], dependencies=[Depends(require_token)])


@router.get("")
async def list_scripts(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(InteractionScript).order_by(InteractionScript.name))).scalars().all()
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "platform": r.platform,
            "enabled": r.enabled,
            "steps": r.steps,
            "trigger": r.trigger,
        }
        for r in rows
    ]


@router.post("")
async def upsert(body: ScriptIn, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(InteractionScript).where(InteractionScript.name == body.name))).scalar_one_or_none()
    if existing:
        existing.platform = body.platform
        existing.enabled = body.enabled
        existing.steps = body.steps
        existing.trigger = body.trigger
        row = existing
    else:
        row = InteractionScript(**body.model_dump())
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"id": str(row.id), "name": row.name}


@router.delete("/{script_id}")
async def delete_script(script_id: str, db: AsyncSession = Depends(get_db)):
    row = await db.get(InteractionScript, script_id)
    if not row:
        raise HTTPException(404, "script not found")
    await db.delete(row)
    await db.commit()
    return {"ok": True}
