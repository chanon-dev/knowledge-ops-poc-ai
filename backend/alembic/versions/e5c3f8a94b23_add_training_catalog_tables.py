"""add training catalog tables (training_methods, base_model_catalog, deployment_targets, training_jobs)

Revision ID: e5c3f8a94b23
Revises: d4b2e7f83a12
Create Date: 2026-02-15 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from uuid import uuid4

# revision identifiers, used by Alembic.
revision = 'e5c3f8a94b23'
down_revision = 'd4b2e7f83a12'
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Seed data — inserted for every existing tenant after table creation
# ---------------------------------------------------------------------------

SEED_METHODS = [
    {
        "name": "LoRA",
        "method_key": "lora",
        "description": "Low-Rank Adaptation — fine-tune เร็ว ใช้ RAM น้อย เหมาะกับโมเดลขนาดเล็ก-กลาง",
        "default_config": {"lora_r": 16, "lora_alpha": 32, "lora_dropout": 0.05},
    },
]

SEED_BASE_MODELS = [
    {
        "model_name": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "display_name": "TinyLlama 1.1B Chat",
        "size_billion": 1.1,
        "recommended_ram_gb": 4,
        "default_target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
    },
]

SEED_TARGETS = [
    {
        "name": "Local Ollama",
        "target_key": "ollama",
        "config": {"temperature": 0.7, "top_p": 0.9, "num_ctx": 4096},
    },
]


def _seed_catalog(tenant_ids: list) -> None:
    """Insert default catalog rows for each tenant."""
    methods_table = sa.table(
        "training_methods",
        sa.column("id", sa.UUID),
        sa.column("tenant_id", sa.UUID),
        sa.column("name", sa.String),
        sa.column("method_key", sa.String),
        sa.column("description", sa.Text),
        sa.column("default_config", postgresql.JSONB),
    )
    base_models_table = sa.table(
        "base_model_catalog",
        sa.column("id", sa.UUID),
        sa.column("tenant_id", sa.UUID),
        sa.column("model_name", sa.String),
        sa.column("display_name", sa.String),
        sa.column("size_billion", sa.Float),
        sa.column("recommended_ram_gb", sa.Float),
        sa.column("default_target_modules", postgresql.JSONB),
    )
    targets_table = sa.table(
        "deployment_targets",
        sa.column("id", sa.UUID),
        sa.column("tenant_id", sa.UUID),
        sa.column("name", sa.String),
        sa.column("target_key", sa.String),
        sa.column("config", postgresql.JSONB),
    )

    for tid in tenant_ids:
        for m in SEED_METHODS:
            op.bulk_insert(methods_table, [{"id": uuid4(), "tenant_id": tid, **m}])
        for bm in SEED_BASE_MODELS:
            op.bulk_insert(base_models_table, [{"id": uuid4(), "tenant_id": tid, **bm}])
        for t in SEED_TARGETS:
            op.bulk_insert(targets_table, [{"id": uuid4(), "tenant_id": tid, **t}])


def upgrade() -> None:
    # --- training_methods ---
    op.create_table('training_methods',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('method_key', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('default_config', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_training_methods_tenant_name'),
    )
    op.create_index(op.f('ix_training_methods_tenant_id'), 'training_methods', ['tenant_id'], unique=False)

    # --- base_model_catalog ---
    op.create_table('base_model_catalog',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('model_name', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('size_billion', sa.Float(), nullable=True),
        sa.Column('recommended_ram_gb', sa.Float(), nullable=True),
        sa.Column('default_target_modules', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'model_name', name='uq_base_model_catalog_tenant_model'),
    )
    op.create_index(op.f('ix_base_model_catalog_tenant_id'), 'base_model_catalog', ['tenant_id'], unique=False)

    # --- deployment_targets ---
    op.create_table('deployment_targets',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('target_key', sa.String(length=50), nullable=False),
        sa.Column('config', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_deployment_targets_tenant_name'),
    )
    op.create_index(op.f('ix_deployment_targets_tenant_id'), 'deployment_targets', ['tenant_id'], unique=False)

    # --- training_jobs ---
    op.create_table('training_jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('method_id', sa.UUID(), nullable=True),
        sa.Column('base_model_id', sa.UUID(), nullable=True),
        sa.Column('deployment_target_id', sa.UUID(), nullable=True),
        sa.Column('base_model_name', sa.String(length=255), nullable=False),
        sa.Column('method_key', sa.String(length=50), nullable=False, server_default=sa.text("'lora'")),
        sa.Column('config', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default=sa.text("'queued'")),
        sa.Column('progress', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('metrics', postgresql.JSONB(), nullable=True),
        sa.Column('model_name', sa.String(length=255), nullable=True),
        sa.Column('device_info', postgresql.JSONB(), nullable=True),
        sa.Column('deployed_to_target', sa.Boolean(), nullable=True),
        sa.Column('started_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['method_id'], ['training_methods.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['base_model_id'], ['base_model_catalog.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deployment_target_id'], ['deployment_targets.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_training_jobs_tenant_id'), 'training_jobs', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_training_jobs_status'), 'training_jobs', ['status'], unique=False)

    # Seed default catalog for all existing tenants
    conn = op.get_bind()
    tenants = conn.execute(sa.text("SELECT id FROM tenants")).fetchall()
    tenant_ids = [row[0] for row in tenants]
    if tenant_ids:
        _seed_catalog(tenant_ids)


def downgrade() -> None:
    op.drop_index(op.f('ix_training_jobs_status'), table_name='training_jobs')
    op.drop_index(op.f('ix_training_jobs_tenant_id'), table_name='training_jobs')
    op.drop_table('training_jobs')

    op.drop_index(op.f('ix_deployment_targets_tenant_id'), table_name='deployment_targets')
    op.drop_table('deployment_targets')

    op.drop_index(op.f('ix_base_model_catalog_tenant_id'), table_name='base_model_catalog')
    op.drop_table('base_model_catalog')

    op.drop_index(op.f('ix_training_methods_tenant_id'), table_name='training_methods')
    op.drop_table('training_methods')
