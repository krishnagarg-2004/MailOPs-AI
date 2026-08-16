from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base_class import Base

if TYPE_CHECKING:
    from backend.app.models.oauth import OAuthAccount


class User(Base):
    """User domain model representing an enterprise MailOps AI user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationship to external OAuth accounts (e.g. Google OAuth)
    oauth_accounts: Mapped[list["OAuthAccount"]] = relationship(
        "OAuthAccount",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', is_active={self.is_active})>"
