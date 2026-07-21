from datetime import datetime
from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class RuntimeHeartbeat(Base):
    __tablename__ = "runtime_heartbeats"
    __table_args__ = (
        Index("ix_system_runtime_heartbeats_type_seen", "worker_type", "last_seen_at"),
        {"schema": "system"},
    )
    worker_name: Mapped[str] = mapped_column(String(128), primary_key=True)
    worker_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, server_default="online")
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict, server_default="{}")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
