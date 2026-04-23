"""row-level security policies for tenant isolation"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0002_rls"
down_revision: str | Sequence[str] | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_SCOPED_TABLES: tuple[str, ...] = (
    "api_key",
    "webhook_endpoint",
    "actor",
    "conversation",
    "event",
    "suspicion_profile",
    "score_history",
    "pattern_match",
    "relationship_edge",
    "response_action",
    "audit_log_entry",
)

ALL_TABLES: tuple[str, ...] = (*TENANT_SCOPED_TABLES, "tenant", "pattern_definition")


def upgrade() -> None:
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sentinel_app"
    )
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sentinel_app")

    for table in TENANT_SCOPED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id::text = current_setting('app.tenant_id', true))
            WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))
            """
        )

    op.execute("ALTER TABLE tenant ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenant FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_self ON tenant
        USING (id::text = current_setting('app.tenant_id', true))
        WITH CHECK (id::text = current_setting('app.tenant_id', true))
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_self ON tenant")
    op.execute("ALTER TABLE tenant NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenant DISABLE ROW LEVEL SECURITY")
    for table in TENANT_SCOPED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.execute(
        "REVOKE SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM sentinel_app"
    )
    op.execute("REVOKE USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public FROM sentinel_app")
