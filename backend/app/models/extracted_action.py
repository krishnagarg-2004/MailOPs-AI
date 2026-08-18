from datetime import datetime
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

if TYPE_CHECKING:
    from backend.app.models.ai_analysis import AIAnalysis
    from backend.app.models.email_message import EmailMessage
    from backend.app.models.email_thread import EmailThread
    from backend.app.models.user import User


class ExtractedAction(Base):
    """Domain model representing granular extracted tasks, decisions, and risks."""

    __tablename__ = "extracted_actions"

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
    ai_analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_messages.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    email_thread_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_threads.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    item_type: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTION")  # ACTION, DECISION, RISK
    description: Mapped[str] = mapped_column(Text, nullable=False)
    assignee: Mapped[str | None] = mapped_column(String(255), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    severity_or_priority: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    evidence_snippet: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_evidence_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")  # PENDING, CONFIRMED, DISMISSED, COMPLETED
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
    user: Mapped["User"] = relationship("User", backref="extracted_actions")
    analysis: Mapped["AIAnalysis"] = relationship("AIAnalysis", back_populates="extracted_items")
    message: Mapped["EmailMessage | None"] = relationship("EmailMessage", backref="extracted_actions")
    thread: Mapped["EmailThread | None"] = relationship("EmailThread", backref="extracted_actions")
