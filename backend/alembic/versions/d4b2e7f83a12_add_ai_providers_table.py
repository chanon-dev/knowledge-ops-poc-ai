"""add_ai_providers_table_and_provider_id_to_allowed_models

Revision ID: d4b2e7f83a12
Revises: c3a1f5d92e01
Create Date: 2026-02-15 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd4b2e7f83a12'
down_revision = 'c3a1f5d92e01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('ai_providers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('provider_type', sa.String(length=50), nullable=False),
        sa.Column('base_url', sa.String(length=500), nullable=False),
        sa.Column('api_key', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_ai_providers_tenant_name'),
    )
    op.create_index(op.f('ix_ai_providers_tenant_id'), 'ai_providers', ['tenant_id'], unique=False)

    op.add_column('allowed_models',
        sa.Column('provider_id', sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        'fk_allowed_models_provider_id',
        'allowed_models', 'ai_providers',
        ['provider_id'], ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_allowed_models_provider_id', 'allowed_models', type_='foreignkey')
    op.drop_column('allowed_models', 'provider_id')
    op.drop_index(op.f('ix_ai_providers_tenant_id'), table_name='ai_providers')
    op.drop_table('ai_providers')
