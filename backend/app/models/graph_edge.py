from datetime import datetime
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint, func, JSON as SQLAlchemyJSON
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base_class import Base

if TYPE_CHECKING:
    from backend.app.models.graph_node import GraphNode
    from backend.app.models.user import User


class GraphEdge(Base):
    """Domain model representing a directed relationship edge between nodes in the Action Graph."""

    __tablename__ = "graph_edges"

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
    source_node_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("graph_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_node_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("graph_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # DEPENDS_ON, BLOCKED_BY, EXTRACTED_FROM, REFERENCES, ASSIGNED_TO, ASSOCIATED_WITH, SUPERSEDES
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    properties: Mapped[dict] = mapped_column(SQLAlchemyJSON, nullable=False, default=dict)
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

    __table_args__ = (
        UniqueConstraint("user_id", "source_node_id", "target_node_id", "relationship_type", name="uq_graph_edge"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="graph_edges")
    source_node: Mapped["GraphNode"] = relationship("GraphNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node: Mapped["GraphNode"] = relationship("GraphNode", foreign_keys=[target_node_id], back_populates="incoming_edges")
