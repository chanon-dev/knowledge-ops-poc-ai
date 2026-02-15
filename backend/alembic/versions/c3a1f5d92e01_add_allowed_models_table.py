"""add_allowed_models_table

Revision ID: c3a1f5d92e01
Revises: 99f67d2f8ac3
Create Date: 2026-02-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c3a1f5d92e01'
down_revision = '99f67d2f8ac3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('allowed_models',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('model_name', sa.String(length=255), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'model_name', name='uq_allowed_models_tenant_model'),
    )
    op.create_index(op.f('ix_allowed_models_tenant_id'), 'allowed_models', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_allowed_models_tenant_id'), table_name='allowed_models')
    op.drop_table('allowed_models')
