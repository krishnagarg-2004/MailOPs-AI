"""create_ai_entities_table

Revision ID: 004_create_ai_entities_table
Revises: 003_create_gmail_entities_table
Create Date: 2026-08-18 15:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_create_ai_entities_table'
down_revision: Union[str, None] = '003_create_gmail_entities_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create ai_analyses table
    op.create_table(
        'ai_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('email_thread_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(length=50), nullable=False, server_default=sa.text("'INFORMATIONAL'")),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default=sa.text("'MEDIUM'")),
        sa.Column('sentiment', sa.String(length=20), nullable=False, server_default=sa.text("'NEUTRAL'")),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default=sa.text('1.0')),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('prompt_version', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default=sa.text("'COMPLETED'")),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['email_message_id'], ['email_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['email_thread_id'], ['email_threads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'email_message_id', 'model_name', 'prompt_version', name='uq_analysis_message_version')
    )
    op.create_index(op.f('ix_ai_analyses_email_message_id'), 'ai_analyses', ['email_message_id'], unique=False)
    op.create_index(op.f('ix_ai_analyses_email_thread_id'), 'ai_analyses', ['email_thread_id'], unique=False)
    op.create_index(op.f('ix_ai_analyses_user_id'), 'ai_analyses', ['user_id'], unique=False)

    # 2. Create extracted_actions table
    op.create_table(
        'extracted_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ai_analysis_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('email_thread_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('item_type', sa.String(length=20), nullable=False, server_default=sa.text("'ACTION'")),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('assignee', sa.String(length=255), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('severity_or_priority', sa.String(length=20), nullable=False, server_default=sa.text("'MEDIUM'")),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default=sa.text('1.0')),
        sa.Column('evidence_snippet', sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column('is_evidence_valid', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('status', sa.String(length=20), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['ai_analysis_id'], ['ai_analyses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['email_message_id'], ['email_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['email_thread_id'], ['email_threads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_extracted_actions_ai_analysis_id'), 'extracted_actions', ['ai_analysis_id'], unique=False)
    op.create_index(op.f('ix_extracted_actions_email_message_id'), 'extracted_actions', ['email_message_id'], unique=False)
    op.create_index(op.f('ix_extracted_actions_email_thread_id'), 'extracted_actions', ['email_thread_id'], unique=False)
    op.create_index(op.f('ix_extracted_actions_user_id'), 'extracted_actions', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_extracted_actions_user_id'), table_name='extracted_actions')
    op.drop_index(op.f('ix_extracted_actions_email_thread_id'), table_name='extracted_actions')
    op.drop_index(op.f('ix_extracted_actions_email_message_id'), table_name='extracted_actions')
    op.drop_index(op.f('ix_extracted_actions_ai_analysis_id'), table_name='extracted_actions')
    op.drop_table('extracted_actions')
    op.drop_index(op.f('ix_ai_analyses_user_id'), table_name='ai_analyses')
    op.drop_index(op.f('ix_ai_analyses_email_thread_id'), table_name='ai_analyses')
    op.drop_index(op.f('ix_ai_analyses_email_message_id'), table_name='ai_analyses')
    op.drop_table('ai_analyses')
