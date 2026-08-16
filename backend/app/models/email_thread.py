from datetime import datetime
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

if TYPE_CHECKING:
    from backend.app.models.email_message import EmailMessage
    from backend.app.models.user import User


class EmailThread(Base):
    """Domain model representing a Gmail email thread container."""

    __tablename__ = "email_threads"
    __table_args__ = (
        UniqueConstraint("user_id", "gmail_thread_id", name="uq_user_gmail_thread"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gmail_thread_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    history_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
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
    user: Mapped["User"] = relationship("User", backref="email_threads")
    messages: Mapped[list["EmailMessage"]] = relationship(
        "EmailMessage",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="EmailMessage.received_at",
    )
