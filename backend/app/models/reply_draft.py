from datetime import datetime
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

if TYPE_CHECKING:
    from backend.app.models.email_message import EmailMessage
    from backend.app.models.email_thread import EmailThread
    from backend.app.models.user import User


class ReplyDraft(Base):
    """Domain model representing a Human-in-the-Loop AI generated email reply draft."""

    __tablename__ = "reply_drafts"

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
    email_thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email_message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gmail_draft_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    intent: Mapped[str] = mapped_column(String(50), nullable=False, default="REPLY_RESPONSE")
    tone: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PROFESSIONAL"
    )  # Controlled Enum: PROFESSIONAL, CONCISE, URGENT, EMPATHETIC
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="DRAFTED", index=True
    )  # DRAFTED, EDITED, APPROVED, SENT, DISCARDED
    rationale_and_provenance: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
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
    user: Mapped["User"] = relationship("User", backref="reply_drafts")
    email_thread: Mapped["EmailThread"] = relationship("EmailThread", backref="reply_drafts")
    email_message: Mapped["EmailMessage"] = relationship("EmailMessage", backref="reply_drafts")
