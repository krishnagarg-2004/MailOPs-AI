import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base_class import Base

if TYPE_CHECKING:
    from backend.app.models.user import User


class OAuthAccount(Base):
    """OAuth account domain model representing an external identity provider account.
    
    SECURITY BOUNDARY NOTE:
    Token fields (encrypted_access_token, encrypted_refresh_token) establish the database
    storage schema for OAuth credentials. In Milestone 3, application-level symmetric
    encryption (e.g. Fernet / AES-256) will encrypt tokens before persistence. Plaintext
    tokens MUST NEVER be stored in these columns or committed to source control.
    """

    __tablename__ = "oauth_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    provider_account_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    encrypted_access_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    encrypted_refresh_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    scopes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationship back to owning User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="oauth_accounts",
    )

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_account_id",
            name="uq_oauth_provider_account",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<OAuthAccount(id={self.id}, user_id={self.user_id}, "
            f"provider='{self.provider}', provider_account_id='{self.provider_account_id}')>"
        )
