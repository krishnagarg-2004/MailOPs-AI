from datetime import datetime
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

if TYPE_CHECKING:
    from backend.app.models.email_message import EmailMessage
    from backend.app.models.email_thread import EmailThread
    from backend.app.models.extracted_action import ExtractedAction
    from backend.app.models.user import User


class AIAnalysis(Base):
    """Domain model representing an AI extraction analysis result for an email or thread."""

    __tablename__ = "ai_analyses"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "email_message_id",
            "model_name",
            "prompt_version",
            name="uq_analysis_message_version",
        ),
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
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str] = mapped_column(String(50), nullable=False, default="INFORMATIONAL")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    sentiment: Mapped[str] = mapped_column(String(20), nullable=False, default="NEUTRAL")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="COMPLETED")
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
    user: Mapped["User"] = relationship("User", backref="ai_analyses")
    message: Mapped["EmailMessage | None"] = relationship("EmailMessage", backref="ai_analyses")
    thread: Mapped["EmailThread | None"] = relationship("EmailThread", backref="ai_analyses")
    extracted_items: Mapped[list["ExtractedAction"]] = relationship(
        "ExtractedAction",
        back_populates="analysis",
        cascade="all, delete-orphan",
    )
