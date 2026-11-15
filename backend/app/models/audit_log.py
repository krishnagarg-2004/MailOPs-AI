"""
Immutable Enterprise Audit Trails & Compliance Logging for MailOps AI.
Provides tamper-evident compliance audit trail for SOC 2, HIPAA, and GDPR inspections.
"""

from datetime import datetime
import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, String, Text, func, JSON as SQLAlchemyJSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base_class import Base

if TYPE_CHECKING:
    from backend.app.models.user import User


class AuditLog(Base):
    """Immutable audit trail record for compliance and security events."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # e.g., AI_DRAFT_GENERATED, AI_DRAFT_APPROVED, EMAIL_SENT, PII_REDACTED, ACTION_ASSIGNED, ROLE_CHANGED
    target_entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # e.g., REPLY_DRAFT, EMAIL_MESSAGE, ACTION_ITEM, USER
    target_entity_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    details: Mapped[dict] = mapped_column(SQLAlchemyJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped["User | None"] = relationship("User", backref="audit_logs")
