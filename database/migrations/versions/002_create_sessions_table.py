"""create_sessions_table

Revision ID: 002_create_sessions_table
Revises: 001_initial_user_and_oauth
Create Date: 2026-08-17 02:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_create_sessions_table"
down_revision: Union[str, None] = "001_initial_user_and_oauth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessions")),
    )
    op.create_index(
        op.f("ix_sessions_session_token_hash"),
        "sessions",
        ["session_token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_sessions_user_id"),
        "sessions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sessions_expires_at"),
        "sessions",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_sessions_expires_at"), table_name="sessions", if_exists=True)
    op.drop_index(op.f("ix_sessions_user_id"), table_name="sessions", if_exists=True)
    op.drop_index(op.f("ix_sessions_session_token_hash"), table_name="sessions", if_exists=True)
    op.drop_table("sessions", if_exists=True)
