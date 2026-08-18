"""create_reply_drafts_table

Revision ID: 008_create_reply_drafts
Revises: 007_create_graph_tables
Create Date: 2026-08-18 16:12:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '008_create_reply_drafts'
down_revision: Union[str, None] = '007_create_graph_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'reply_drafts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email_thread_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email_message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gmail_draft_id', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('body_text', sa.Text(), nullable=False),
        sa.Column('recipient_email', sa.String(length=255), nullable=False),
        sa.Column('intent', sa.String(length=50), nullable=False, server_default='REPLY_RESPONSE'),
        sa.Column('tone', sa.String(length=50), nullable=False, server_default='PROFESSIONAL'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFTED'),
        sa.Column('rationale_and_provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['email_message_id'], ['email_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['email_thread_id'], ['email_threads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reply_drafts_email_message_id'), 'reply_drafts', ['email_message_id'], unique=False)
    op.create_index(op.f('ix_reply_drafts_email_thread_id'), 'reply_drafts', ['email_thread_id'], unique=False)
    op.create_index(op.f('ix_reply_drafts_gmail_draft_id'), 'reply_drafts', ['gmail_draft_id'], unique=False)
    op.create_index(op.f('ix_reply_drafts_status'), 'reply_drafts', ['status'], unique=False)
    op.create_index(op.f('ix_reply_drafts_user_id'), 'reply_drafts', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_reply_drafts_user_id'), table_name='reply_drafts')
    op.drop_index(op.f('ix_reply_drafts_status'), table_name='reply_drafts')
    op.drop_index(op.f('ix_reply_drafts_gmail_draft_id'), table_name='reply_drafts')
    op.drop_index(op.f('ix_reply_drafts_email_thread_id'), table_name='reply_drafts')
    op.drop_index(op.f('ix_reply_drafts_email_message_id'), table_name='reply_drafts')
    op.drop_table('reply_drafts')
