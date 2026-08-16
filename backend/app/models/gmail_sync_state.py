from datetime import datetime
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

if TYPE_CHECKING:
    from backend.app.models.user import User


class GmailSyncState(Base):
    """Domain model tracking per-user Gmail synchronization state and progress."""

    __tablename__ = "gmail_sync_states"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    last_history_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    sync_status: Mapped[str] = mapped_column(
        String(50),
        default="IDLE",
        nullable=False,
        comment="Current status: IDLE, SYNCING, COMPLETED, FAILED",
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    synced_message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="gmail_sync_state")
