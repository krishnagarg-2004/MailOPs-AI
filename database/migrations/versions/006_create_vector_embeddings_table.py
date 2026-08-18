"""create_vector_embeddings_table

Revision ID: 006_create_vector_embeddings
Revises: 005_create_doc_extractions
Create Date: 2026-08-18 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '006_create_vector_embeddings'
down_revision: Union[str, None] = '005_create_doc_extractions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Create vector_embeddings table
    op.create_table(
        'vector_embeddings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_type', sa.String(length=20), nullable=False, server_default=sa.text("'EMAIL'")),
        sa.Column('email_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('attachment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('document_extraction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('chunk_index', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('embedding', Vector(768), nullable=False),
        sa.Column('embedding_model', sa.String(length=50), nullable=False, server_default=sa.text("'text-embedding-004'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['attachment_id'], ['attachments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_extraction_id'], ['document_extractions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['email_message_id'], ['email_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vector_embeddings_attachment_id'), 'vector_embeddings', ['attachment_id'], unique=False)
    op.create_index(op.f('ix_vector_embeddings_document_extraction_id'), 'vector_embeddings', ['document_extraction_id'], unique=False)
    op.create_index(op.f('ix_vector_embeddings_email_message_id'), 'vector_embeddings', ['email_message_id'], unique=False)
    op.create_index(op.f('ix_vector_embeddings_user_id'), 'vector_embeddings', ['user_id'], unique=False)

    # 3. Create HNSW Cosine Index for pgvector
    op.execute("CREATE INDEX IF NOT EXISTS ix_vector_embeddings_embedding ON vector_embeddings USING hnsw (embedding vector_cosine_ops);")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_vector_embeddings_embedding;")
    op.drop_index(op.f('ix_vector_embeddings_user_id'), table_name='vector_embeddings')
    op.drop_index(op.f('ix_vector_embeddings_email_message_id'), table_name='vector_embeddings')
    op.drop_index(op.f('ix_vector_embeddings_document_extraction_id'), table_name='vector_embeddings')
    op.drop_index(op.f('ix_vector_embeddings_attachment_id'), table_name='vector_embeddings')
    op.drop_table('vector_embeddings')
