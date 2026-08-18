"""create_graph_tables

Revision ID: 007_create_graph_tables
Revises: 006_create_vector_embeddings
Create Date: 2026-08-18 16:06:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '007_create_graph_tables'
down_revision: Union[str, None] = '006_create_vector_embeddings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create graph_nodes table
    op.create_table(
        'graph_nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('node_type', sa.String(length=50), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('entity_reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('properties', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_graph_nodes_entity_reference_id'), 'graph_nodes', ['entity_reference_id'], unique=False)
    op.create_index(op.f('ix_graph_nodes_node_type'), 'graph_nodes', ['node_type'], unique=False)
    op.create_index(op.f('ix_graph_nodes_user_id'), 'graph_nodes', ['user_id'], unique=False)

    # 2. Create graph_edges table
    op.create_table(
        'graph_edges',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_node_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_node_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relationship_type', sa.String(length=50), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False, server_default=sa.text('1.0')),
        sa.Column('properties', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['source_node_id'], ['graph_nodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_node_id'], ['graph_nodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'source_node_id', 'target_node_id', 'relationship_type', name='uq_graph_edge')
    )
    op.create_index(op.f('ix_graph_edges_relationship_type'), 'graph_edges', ['relationship_type'], unique=False)
    op.create_index(op.f('ix_graph_edges_source_node_id'), 'graph_edges', ['source_node_id'], unique=False)
    op.create_index(op.f('ix_graph_edges_target_node_id'), 'graph_edges', ['target_node_id'], unique=False)
    op.create_index(op.f('ix_graph_edges_user_id'), 'graph_edges', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_graph_edges_user_id'), table_name='graph_edges')
    op.drop_index(op.f('ix_graph_edges_target_node_id'), table_name='graph_edges')
    op.drop_index(op.f('ix_graph_edges_source_node_id'), table_name='graph_edges')
    op.drop_index(op.f('ix_graph_edges_relationship_type'), table_name='graph_edges')
    op.drop_table('graph_edges')
    op.drop_index(op.f('ix_graph_nodes_user_id'), table_name='graph_nodes')
    op.drop_index(op.f('ix_graph_nodes_node_type'), table_name='graph_nodes')
    op.drop_index(op.f('ix_graph_nodes_entity_reference_id'), table_name='graph_nodes')
    op.drop_table('graph_nodes')
