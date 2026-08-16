import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

# Naming convention for constraints to ensure Alembic auto-generates predictable names
POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata_obj = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Declarative base class for all MailOps AI SQLAlchemy models."""

    metadata = metadata_obj

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate __tablename__ automatically in pluralized snake_case if not explicitly defined."""
        name = cls.__name__
        # Convert CamelCase to snake_case
        snake = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        if snake.endswith("y") and not snake.endswith(("ay", "ey", "oy", "uy")):
            return snake[:-1] + "ies"
        elif not snake.endswith("s"):
            return snake + "s"
        return snake

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        sort_order=-100,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        sort_order=100,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
        sort_order=101,
    )
