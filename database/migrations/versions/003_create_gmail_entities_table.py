"""create_gmail_entities_table

Revision ID: 003_create_gmail_entities_table
Revises: 002_create_sessions_table
Create Date: 2026-08-17 03:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_create_gmail_entities_table'
down_revision: Union[str, None] = '002_create_sessions_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create email_threads table
    op.create_table(
        'email_threads',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gmail_thread_id', sa.String(length=255), nullable=False),
        sa.Column('snippet', sa.Text(), nullable=True),
        sa.Column('history_id', sa.BigInteger(), nullable=True),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'gmail_thread_id', name='uq_user_gmail_thread')
    )
    op.create_index(op.f('ix_email_threads_gmail_thread_id'), 'email_threads', ['gmail_thread_id'], unique=False)
    op.create_index(op.f('ix_email_threads_last_message_at'), 'email_threads', ['last_message_at'], unique=False)
    op.create_index(op.f('ix_email_threads_user_id'), 'email_threads', ['user_id'], unique=False)

    # 2. Create email_messages table
    op.create_table(
        'email_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gmail_message_id', sa.String(length=255), nullable=False),
        sa.Column('gmail_thread_id', sa.String(length=255), nullable=False),
        sa.Column('history_id', sa.BigInteger(), nullable=True),
        sa.Column('sender', sa.String(length=255), nullable=True),
        sa.Column('recipients', sa.Text(), nullable=True),
        sa.Column('subject', sa.String(length=512), nullable=True),
        sa.Column('snippet', sa.Text(), nullable=True),
        sa.Column('body_plain', sa.Text(), nullable=True),
        sa.Column('body_html', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('labels', sa.Text(), nullable=True, comment="JSON string storing array of Gmail provider label IDs e.g. ['INBOX', 'UNREAD']"),
        sa.Column('has_attachments', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['thread_id'], ['email_threads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'gmail_message_id', name='uq_user_gmail_message')
    )
    op.create_index(op.f('ix_email_messages_gmail_message_id'), 'email_messages', ['gmail_message_id'], unique=False)
    op.create_index(op.f('ix_email_messages_gmail_thread_id'), 'email_messages', ['gmail_thread_id'], unique=False)
    op.create_index(op.f('ix_email_messages_received_at'), 'email_messages', ['received_at'], unique=False)
    op.create_index(op.f('ix_email_messages_sender'), 'email_messages', ['sender'], unique=False)
    op.create_index(op.f('ix_email_messages_sent_at'), 'email_messages', ['sent_at'], unique=False)
    op.create_index(op.f('ix_email_messages_thread_id'), 'email_messages', ['thread_id'], unique=False)
    op.create_index(op.f('ix_email_messages_user_id'), 'email_messages', ['user_id'], unique=False)

    # 3. Create attachments table
    op.create_table(
        'attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gmail_attachment_id', sa.String(length=512), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=128), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('storage_path', sa.String(length=512), nullable=True, comment="Relative disk storage path using sanitized UUID filename"),
        sa.Column('is_downloaded', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['email_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attachments_message_id'), 'attachments', ['message_id'], unique=False)
    op.create_index(op.f('ix_attachments_user_id'), 'attachments', ['user_id'], unique=False)

    # 4. Create gmail_sync_states table
    op.create_table(
        'gmail_sync_states',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('last_history_id', sa.BigInteger(), nullable=True),
        sa.Column('sync_status', sa.String(length=50), nullable=False, server_default=sa.text("'IDLE'"), comment="Current status: IDLE, SYNCING, COMPLETED, FAILED"),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('synced_message_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_gmail_sync_states_user_id'), 'gmail_sync_states', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_gmail_sync_states_user_id'), table_name='gmail_sync_states')
    op.drop_table('gmail_sync_states')
    op.drop_index(op.f('ix_attachments_user_id'), table_name='attachments')
    op.drop_index(op.f('ix_attachments_message_id'), table_name='attachments')
    op.drop_table('attachments')
    op.drop_index(op.f('ix_email_messages_user_id'), table_name='email_messages')
    op.drop_index(op.f('ix_email_messages_thread_id'), table_name='email_messages')
    op.drop_index(op.f('ix_email_messages_sent_at'), table_name='email_messages')
    op.drop_index(op.f('ix_email_messages_sender'), table_name='email_messages')
    op.drop_index(op.f('ix_email_messages_received_at'), table_name='email_messages')
    op.drop_index(op.f('ix_email_messages_gmail_thread_id'), table_name='email_messages')
    op.drop_index(op.f('ix_email_messages_gmail_message_id'), table_name='email_messages')
    op.drop_table('email_messages')
    op.drop_index(op.f('ix_email_threads_user_id'), table_name='email_threads')
    op.drop_index(op.f('ix_email_threads_last_message_at'), table_name='email_threads')
    op.drop_index(op.f('ix_email_threads_gmail_thread_id'), table_name='email_threads')
    op.drop_table('email_threads')
