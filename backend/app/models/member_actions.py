import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.core import Base


class MemberActionType(str, enum.Enum):
    SEND_DM = "send_dm"
    RENAME = "rename"
    KICK = "kick"
    BAN = "ban"
    ADD_ROLE = "add_role"
    REMOVE_ROLE = "remove_role"
    SHIELDNET_BLOCK = "shieldnet_block"
    SHIELDNET_UNBLOCK = "shieldnet_unblock"


class MemberActionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MemberAction(Base):
    __tablename__ = "member_actions"
    __table_args__ = (
        Index("ix_discord_member_actions_queue", "guild_id", "status", "created_at"),
        {"schema": "discord"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    discord_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action_type: Mapped[MemberActionType] = mapped_column(
        Enum(MemberActionType, name="member_action_type", schema="discord",
             values_callable=lambda c: [i.value for i in c]),
        nullable=False,
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    status: Mapped[MemberActionStatus] = mapped_column(
        Enum(MemberActionStatus, name="member_action_status", schema="discord",
             values_callable=lambda c: [i.value for i in c]),
        nullable=False,
        default=MemberActionStatus.PENDING,
        server_default="pending",
    )
    requested_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("core.users.id", ondelete="SET NULL"),
    )
    result_message: Mapped[str | None] = mapped_column(Text)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
