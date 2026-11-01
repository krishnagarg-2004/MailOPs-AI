from datetime import datetime
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Float, ForeignKey, JSON as SQLAlchemyJSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

if TYPE_CHECKING:
    from backend.app.models.attachment import Attachment
    from backend.app.models.document_extraction import DocumentExtraction
    from backend.app.models.user import User


class BusinessDocumentExtraction(Base):
    """Domain model representing Layer 2 domain-specific business intelligence parsed from documents (Invoices, Contracts)."""

    __tablename__ = "business_document_extractions"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attachment_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("attachments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_extraction_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("document_extractions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="OTHER"
    )  # INVOICE, CONTRACT, RECEIPT, PURCHASE_ORDER, OTHER
    extracted_data: Mapped[dict] = mapped_column(
        SQLAlchemyJSON, nullable=False, default=dict
    )  # Full JSON payload adhering to InvoiceExtractionSchema or ContractExtractionSchema
    vendor_or_party: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_or_expiration_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    financial_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
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
    user: Mapped["User"] = relationship("User", backref="business_document_extractions")
    attachment: Mapped["Attachment"] = relationship("Attachment", backref="business_extractions")
    document_extraction: Mapped["DocumentExtraction"] = relationship(
        "DocumentExtraction", back_populates="business_extractions"
    )
