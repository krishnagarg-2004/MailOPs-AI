from datetime import datetime
import uuid
from typing import TYPE_CHECKING
from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.config import settings
from backend.app.db.base_class import Base

if TYPE_CHECKING:
    from backend.app.models.attachment import Attachment
    from backend.app.models.document_extraction import DocumentExtraction
    from backend.app.models.email_message import EmailMessage
    from backend.app.models.user import User


class VectorEmbedding(Base):
    """Domain model representing text chunks and vector embeddings stored in pgvector."""

    __tablename__ = "vector_embeddings"

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
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="EMAIL"
    )  # EMAIL, DOCUMENT
    email_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_messages.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    attachment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("attachments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    document_extraction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_extractions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # 768-dimensional vector embedding column (pgvector)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(settings.EMBEDDING_DIMENSION),
        nullable=False,
    )
    embedding_model: Mapped[str] = mapped_column(
        String(50), nullable=False, default=settings.EMBEDDING_MODEL
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
    user: Mapped["User"] = relationship("User", backref="vector_embeddings")
    message: Mapped["EmailMessage"] = relationship("EmailMessage", backref="vector_embeddings")
    attachment: Mapped["Attachment"] = relationship("Attachment", backref="vector_embeddings")
    document_extraction: Mapped["DocumentExtraction"] = relationship("DocumentExtraction", backref="vector_embeddings")
