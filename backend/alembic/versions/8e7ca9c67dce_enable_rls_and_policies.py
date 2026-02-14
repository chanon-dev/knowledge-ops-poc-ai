"""enable_rls_and_policies

Revision ID: 8e7ca9c67dce
Revises: b6a86a81b3c8
Create Date: 2026-02-12 23:57:13.361451

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '8e7ca9c67dce'
down_revision = 'b6a86a81b3c8'
branch_labels = None
depends_on = None

TENANT_SCOPED_TABLES = [
    "users",
    "departments",
    "department_members",
    "knowledge_docs",
    "knowledge_chunks",
    "conversations",
    "messages",
    "approvals",
    "audit_logs",
    "api_keys",
]


def upgrade() -> None:
    for table in TENANT_SCOPED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

        op.execute(f"""
            CREATE POLICY tenant_read ON {table} FOR SELECT
            USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
        """)
        op.execute(f"""
            CREATE POLICY tenant_insert ON {table} FOR INSERT
            WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid)
        """)
        op.execute(f"""
            CREATE POLICY tenant_update ON {table} FOR UPDATE
            USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
        """)
        op.execute(f"""
            CREATE POLICY tenant_delete ON {table} FOR DELETE
            USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
        """)


def downgrade() -> None:
    for table in TENANT_SCOPED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_read ON {table}")
        op.execute(f"DROP POLICY IF EXISTS tenant_insert ON {table}")
        op.execute(f"DROP POLICY IF EXISTS tenant_update ON {table}")
        op.execute(f"DROP POLICY IF EXISTS tenant_delete ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
