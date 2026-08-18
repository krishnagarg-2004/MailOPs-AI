"""create_document_extractions_table

Revision ID: 005_create_document_extractions_table
Revises: 004_create_ai_entities_table
Create Date: 2026-08-18 15:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_create_doc_extractions'
down_revision: Union[str, None] = '004_create_ai_entities_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create document_extractions table
    op.create_table(
        'document_extractions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attachment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email_message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_type', sa.String(length=20), nullable=False),
        sa.Column('extraction_method', sa.String(length=50), nullable=False, server_default=sa.text("'NATIVE_TEXT'")),
        sa.Column('extracted_text', sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column('char_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('is_ocr_applied', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('status', sa.String(length=20), nullable=False, server_default=sa.text("'COMPLETED'")),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['attachment_id'], ['attachments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['email_message_id'], ['email_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('attachment_id')
    )
    op.create_index(op.f('ix_document_extractions_attachment_id'), 'document_extractions', ['attachment_id'], unique=True)
    op.create_index(op.f('ix_document_extractions_email_message_id'), 'document_extractions', ['email_message_id'], unique=False)
    op.create_index(op.f('ix_document_extractions_user_id'), 'document_extractions', ['user_id'], unique=False)

    # 2. Create business_document_extractions table
    op.create_table(
        'business_document_extractions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attachment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_extraction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_category', sa.String(length=50), nullable=False, server_default=sa.text("'OTHER'")),
        sa.Column('extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('vendor_or_party', sa.String(length=255), nullable=True),
        sa.Column('document_reference_number', sa.String(length=100), nullable=True),
        sa.Column('document_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_or_expiration_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('financial_total', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default=sa.text('1.0')),
        sa.Column('status', sa.String(length=20), nullable=False, server_default=sa.text("'COMPLETED'")),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['attachment_id'], ['attachments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_extraction_id'], ['document_extractions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_business_document_extractions_attachment_id'), 'business_document_extractions', ['attachment_id'], unique=False)
    op.create_index(op.f('ix_business_document_extractions_document_extraction_id'), 'business_document_extractions', ['document_extraction_id'], unique=False)
    op.create_index(op.f('ix_business_document_extractions_user_id'), 'business_document_extractions', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_business_document_extractions_user_id'), table_name='business_document_extractions')
    op.drop_index(op.f('ix_business_document_extractions_document_extraction_id'), table_name='business_document_extractions')
    op.drop_index(op.f('ix_business_document_extractions_attachment_id'), table_name='business_document_extractions')
    op.drop_table('business_document_extractions')
    op.drop_index(op.f('ix_document_extractions_user_id'), table_name='document_extractions')
    op.drop_index(op.f('ix_document_extractions_email_message_id'), table_name='document_extractions')
    op.drop_index(op.f('ix_document_extractions_attachment_id'), table_name='document_extractions')
    op.drop_table('document_extractions')
