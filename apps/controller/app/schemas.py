from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    username: str
    password: str
    platform: str = "kick"
    totp: str | None = None
    notes: str | None = None
    assigned_worker_id: str | None = None


class AccountOut(BaseModel):
    id: UUID
    username: str
    platform: str
    status: str
    health_score: int
    last_login_at: datetime | None
    assigned_worker_id: str | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProvisionRequest(BaseModel):
    username: str
    password: str
    channel: str
    worker_id: str | None = None
    notes: str | None = "authorized test account"


class WorkerHeartbeat(BaseModel):
    id: str
    name: str
    status: str
    cpu_percent: float
    ram_mb: float
    ram_limit_mb: float | None = None
    novnc_url: str | None = None
    vnc_port: int | None = None
    labels: dict[str, Any] = Field(default_factory=dict)
    snapshot_jpeg_b64: str | None = None


class WorkerOut(BaseModel):
    id: str
    name: str
    status: str
    cpu_percent: float
    ram_mb: float
    ram_limit_mb: float | None
    novnc_url: str | None
    last_heartbeat_at: datetime | None
    labels: dict[str, Any]
    has_snapshot: bool = False


class TaskCreate(BaseModel):
    type: str
    worker_id: str | None = None
    account_id: UUID | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    run_at: datetime | None = None


class TaskOut(BaseModel):
    id: UUID
    type: str
    status: str
    worker_id: str | None
    account_id: UUID | None
    payload: dict[str, Any]
    result: dict[str, Any] | None
    error: str | None
    run_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskClaimOut(BaseModel):
    task: TaskOut | None = None
    credentials: dict[str, Any] | None = None
    storage_state: dict[str, Any] | None = None


class TaskReport(BaseModel):
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None
    storage_state: dict[str, Any] | None = None
    account_status: str | None = None
    health_delta: int | None = None


class ChatIn(BaseModel):
    account_id: UUID | None = None
    worker_id: str | None = None
    channel: str
    direction: str
    body: str


class ChatDispatch(BaseModel):
    channel: str
    text: str
    account_ids: list[UUID] | None = None
    worker_ids: list[str] | None = None
    script_name: str | None = None


class ScriptIn(BaseModel):
    name: str
    platform: str = "kick"
    enabled: bool = True
    steps: list[dict[str, Any]]
    trigger: dict[str, Any] | None = None


class LogIn(BaseModel):
    worker_id: str | None = None
    level: str = "info"
    message: str
    extra: dict[str, Any] = Field(default_factory=dict)
