"""add status_message to training_jobs

Revision ID: f6d4a9b05c34
Revises: e5c3f8a94b23
Create Date: 2026-02-15 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f6d4a9b05c34'
down_revision = 'e5c3f8a94b23'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('training_jobs', sa.Column('status_message', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('training_jobs', 'status_message')
