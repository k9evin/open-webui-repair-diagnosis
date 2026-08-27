"""add repair diagnosis tables

Revision ID: e5f6a7b8c9d0
Revises: d4c1a8e37b62
Create Date: 2026-08-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'e5f6a7b8c9d0'
down_revision: str | None = 'd4c1a8e37b62'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'repair_case',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('source_file', sa.Text(), nullable=True),
        sa.Column('source_row_id', sa.Text(), nullable=True),
        sa.Column('raw_record_json', sa.JSON(), nullable=False),
        sa.Column('pn_raw', sa.Text(), nullable=False),
        sa.Column('pn_normalized', sa.Text(), nullable=False),
        sa.Column('sn', sa.Text(), nullable=True),
        sa.Column('product_type', sa.Text(), nullable=False),
        sa.Column('product_family', sa.Text(), nullable=True),
        sa.Column('plant', sa.Text(), nullable=True),
        sa.Column('failure_type', sa.Text(), nullable=True),
        sa.Column('failure_description_raw', sa.Text(), nullable=False),
        sa.Column('repair_steps_raw', sa.Text(), nullable=True),
        sa.Column('repair_steps_normalized', sa.Text(), nullable=True),
        sa.Column('test_result_raw', sa.Text(), nullable=True),
        sa.Column('measurement_status', sa.Text(), nullable=False),
        sa.Column('original_part_pn', sa.Text(), nullable=True),
        sa.Column('replacement_part_pn', sa.Text(), nullable=True),
        sa.Column('replacement_part_raw', sa.Text(), nullable=True),
        sa.Column('final_result', sa.Text(), nullable=True),
        sa.Column('retest_result', sa.Text(), nullable=True),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('review_status', sa.Text(), nullable=False),
        sa.Column('case_quality', sa.Text(), nullable=False),
        sa.Column('submitted_by', sa.Text(), nullable=True),
        sa.Column('reviewed_by', sa.Text(), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
    )
    op.create_index('repair_case_pn_normalized_idx', 'repair_case', ['pn_normalized'])
    op.create_index('repair_case_product_type_idx', 'repair_case', ['product_type'])
    op.create_index('repair_case_product_family_idx', 'repair_case', ['product_family'])
    op.create_index('repair_case_failure_type_idx', 'repair_case', ['failure_type'])
    op.create_index('repair_case_review_status_idx', 'repair_case', ['review_status'])
    op.create_table(
        'repair_sop',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('version', sa.Text(), nullable=False),
        sa.Column('product_type', sa.Text(), nullable=False),
        sa.Column('failure_type', sa.Text(), nullable=True),
        sa.Column('applicable_pn', sa.Text(), nullable=True),
        sa.Column('product_family', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('effective_date', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.Text(), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
    )
    op.create_index('repair_sop_product_type_idx', 'repair_sop', ['product_type'])
    op.create_index('repair_sop_failure_type_idx', 'repair_sop', ['failure_type'])
    op.create_table(
        'repair_audit_log',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('case_id', sa.Text(), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
    )
    op.create_index('repair_audit_log_case_id_idx', 'repair_audit_log', ['case_id'])


def downgrade() -> None:
    op.drop_index('repair_audit_log_case_id_idx', table_name='repair_audit_log')
    op.drop_table('repair_audit_log')
    op.drop_index('repair_sop_failure_type_idx', table_name='repair_sop')
    op.drop_index('repair_sop_product_type_idx', table_name='repair_sop')
    op.drop_table('repair_sop')
    op.drop_index('repair_case_review_status_idx', table_name='repair_case')
    op.drop_index('repair_case_failure_type_idx', table_name='repair_case')
    op.drop_index('repair_case_product_family_idx', table_name='repair_case')
    op.drop_index('repair_case_product_type_idx', table_name='repair_case')
    op.drop_index('repair_case_pn_normalized_idx', table_name='repair_case')
    op.drop_table('repair_case')
