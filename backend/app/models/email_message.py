from datetime import datetime
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

if TYPE_CHECKING:
    from backend.app.models.attachment import Attachment
    from backend.app.models.email_thread import EmailThread
    from backend.app.models.user import User


class EmailMessage(Base):
    """Domain model representing a Gmail email message."""

    __tablename__ = "email_messages"
    __table_args__ = (
        UniqueConstraint("user_id", "gmail_message_id", name="uq_user_gmail_message"),
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
    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gmail_message_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    gmail_thread_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    history_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    sender: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    recipients: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_plain: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    labels: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="JSON string storing array of Gmail provider label IDs e.g. ['INBOX', 'UNREAD']",
    )
    has_attachments: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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
    user: Mapped["User"] = relationship("User", backref="email_messages")
    thread: Mapped["EmailThread"] = relationship("EmailThread", back_populates="messages")
    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment",
        back_populates="message",
        cascade="all, delete-orphan",
    )
