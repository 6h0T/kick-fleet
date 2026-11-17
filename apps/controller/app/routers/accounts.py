from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crypto import encrypt_json
from app.db import get_db
from app.deps import require_token
from app.models import Account, Worker
from app.schemas import AccountCreate, AccountOut, ProvisionRequest, TaskCreate
from app.services.tasks import enqueue_task

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"], dependencies=[Depends(require_token)])


@router.get("", response_model=list[AccountOut])
async def list_accounts(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Account).order_by(Account.created_at.desc()))).scalars().all()
    return rows


@router.post("", response_model=AccountOut)
async def create_account(body: AccountCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Account).where(Account.platform == body.platform, Account.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "account already exists")
    account = Account(
        username=body.username,
        platform=body.platform,
        credential_blob=encrypt_json({"password": body.password, "totp": body.totp}),
        status="active",
        assigned_worker_id=body.assigned_worker_id,
        notes=body.notes,
        profile_key=f"{body.platform}:{body.username}",
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@router.post("/provision", response_model=AccountOut)
async def provision(body: ProvisionRequest, db: AsyncSession = Depends(get_db)):
    worker_id = body.worker_id
    if not worker_id:
        idle = (await db.execute(select(Worker).where(Worker.status.in_(["idle", "starting", "busy"])))).scalars().first()
        worker_id = idle.id if idle else None
    if not worker_id:
        raise HTTPException(400, "no worker available for provisioning")
    created = await create_account(
        AccountCreate(
            username=body.username,
            password=body.password,
            notes=body.notes,
            assigned_worker_id=worker_id,
        ),
        db,
    )
    created.status = "provisioning"
    created.assigned_worker_id = worker_id
    await db.commit()
    await db.refresh(created)
    await enqueue_task(
        db,
        TaskCreate(
            type="login",
            worker_id=worker_id,
            account_id=created.id,
            payload={"channel": body.channel},
        ),
    )
    return created


@router.patch("/{account_id}/status", response_model=AccountOut)
async def set_status(account_id: str, status: str, db: AsyncSession = Depends(get_db)):
    account = await db.get(Account, account_id)
    if not account:
        raise HTTPException(404, "account not found")
    account.status = status
    await db.commit()
    await db.refresh(account)
    return account
