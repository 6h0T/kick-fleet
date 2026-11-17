import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, LargeBinary, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(Text)
    platform: Mapped[str] = mapped_column(Text, default="kick")
    credential_blob: Mapped[bytes] = mapped_column(LargeBinary)
    status: Mapped[str] = mapped_column(Text, default="provisioning")
    health_score: Mapped[int] = mapped_column(Integer, default=100)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assigned_worker_id: Mapped[str | None] = mapped_column(Text)
    profile_key: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"))
    worker_id: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="starting")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    storage_state_blob: Mapped[bytes | None] = mapped_column(LargeBinary)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)


class Worker(Base):
    __tablename__ = "workers"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="starting")
    cpu_percent: Mapped[float] = mapped_column(Float, default=0)
    ram_mb: Mapped[float] = mapped_column(Float, default=0)
    ram_limit_mb: Mapped[float | None] = mapped_column(Float)
    novnc_url: Mapped[str | None] = mapped_column(Text)
    vnc_port: Mapped[int | None] = mapped_column(Integer)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    labels: Mapped[dict] = mapped_column(JSONB, default=dict)
    snapshot_jpeg: Mapped[bytes | None] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="queued")
    worker_id: Mapped[str | None] = mapped_column(Text)
    account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    result: Mapped[dict | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"))
    worker_id: Mapped[str | None] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(Text)
    direction: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InteractionScript(Base):
    __tablename__ = "interaction_scripts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, unique=True)
    platform: Mapped[str] = mapped_column(Text, default="kick")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    steps: Mapped[list | dict] = mapped_column(JSONB)
    trigger: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EventLog(Base):
    __tablename__ = "event_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    worker_id: Mapped[str | None] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String, default="info")
    message: Mapped[str] = mapped_column(Text)
    extra: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
