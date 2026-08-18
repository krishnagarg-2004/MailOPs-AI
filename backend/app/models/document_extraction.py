from datetime import datetime
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

if TYPE_CHECKING:
    from backend.app.models.attachment import Attachment
    from backend.app.models.business_document_extraction import BusinessDocumentExtraction
    from backend.app.models.email_message import EmailMessage
    from backend.app.models.user import User


class DocumentExtraction(Base):
    """Domain model representing Layer 1 raw text extraction and OCR metadata for an email attachment."""

    __tablename__ = "document_extractions"

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
    attachment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("attachments.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    email_message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # PDF, DOCX, IMAGE
    extraction_method: Mapped[str] = mapped_column(
        String(50), nullable=False, default="NATIVE_TEXT"
    )  # NATIVE_TEXT, OCR_TESSERACT, HYBRID
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    char_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_ocr_applied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="COMPLETED")  # COMPLETED, FAILED, PENDING
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
    user: Mapped["User"] = relationship("User", backref="document_extractions")
    attachment: Mapped["Attachment"] = relationship("Attachment", backref="extraction", uselist=False)
    message: Mapped["EmailMessage"] = relationship("EmailMessage", backref="document_extractions")
    business_extractions: Mapped[list["BusinessDocumentExtraction"]] = relationship(
        "BusinessDocumentExtraction",
        back_populates="document_extraction",
        cascade="all, delete-orphan",
    )
