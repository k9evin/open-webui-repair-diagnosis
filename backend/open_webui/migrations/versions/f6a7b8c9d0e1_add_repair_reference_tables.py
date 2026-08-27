"""add repair reference tables

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'f6a7b8c9d0e1'
down_revision: str | None = 'e5f6a7b8c9d0'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'repair_reference_document',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('file_id', sa.Text(), nullable=False, unique=True),
        sa.Column('document_type', sa.Text(), nullable=False),
        sa.Column('version', sa.Text(), nullable=True),
        sa.Column('source_name', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('pn_normalized', sa.JSON(), nullable=False),
        sa.Column('product_family', sa.Text(), nullable=True),
        sa.Column('product_type', sa.Text(), nullable=True),
        sa.Column('failure_type', sa.Text(), nullable=True),
        sa.Column('plant', sa.Text(), nullable=True),
        sa.Column('extraction_config', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.Text(), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
    )
    op.create_index('repair_reference_document_type_idx', 'repair_reference_document', ['document_type'])
    op.create_index('repair_reference_product_family_idx', 'repair_reference_document', ['product_family'])
    op.create_index('repair_reference_product_type_idx', 'repair_reference_document', ['product_type'])
    op.create_index('repair_reference_failure_type_idx', 'repair_reference_document', ['failure_type'])
    op.create_index('repair_reference_plant_idx', 'repair_reference_document', ['plant'])
    op.create_table(
        'repair_reference_chunk',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('document_id', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.UniqueConstraint('document_id', 'chunk_index', name='repair_reference_chunk_document_index_unique'),
    )
    op.create_index('repair_reference_chunk_document_id_idx', 'repair_reference_chunk', ['document_id'])
    op.create_table(
        'repair_index_version',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('config_hash', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('indexed_at', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
    )
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        op.execute(
            "CREATE VIRTUAL TABLE repair_reference_chunk_fts "
            "USING fts5(id UNINDEXED, content, tokenize='trigram')"
        )
    elif bind.dialect.name == 'postgresql':
        op.execute(
            "CREATE INDEX repair_reference_chunk_content_fts_idx "
            "ON repair_reference_chunk USING gin(to_tsvector('simple', content))"
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        op.execute('DROP TABLE repair_reference_chunk_fts')
    elif bind.dialect.name == 'postgresql':
        op.drop_index('repair_reference_chunk_content_fts_idx', table_name='repair_reference_chunk')
    op.drop_table('repair_index_version')
    op.drop_index('repair_reference_chunk_document_id_idx', table_name='repair_reference_chunk')
    op.drop_table('repair_reference_chunk')
    op.drop_index('repair_reference_plant_idx', table_name='repair_reference_document')
    op.drop_index('repair_reference_failure_type_idx', table_name='repair_reference_document')
    op.drop_index('repair_reference_product_type_idx', table_name='repair_reference_document')
    op.drop_index('repair_reference_product_family_idx', table_name='repair_reference_document')
    op.drop_index('repair_reference_document_type_idx', table_name='repair_reference_document')
    op.drop_table('repair_reference_document')
