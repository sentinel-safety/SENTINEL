"""age graph labels and privileges"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0003_age_graph"
down_revision: str | Sequence[str] | None = "0002_rls"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS age")
    op.execute("LOAD 'age'")
    op.execute("SET LOCAL search_path = ag_catalog, public")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM ag_catalog.ag_graph WHERE name = 'sentinel_graph') THEN
                PERFORM ag_catalog.create_graph('sentinel_graph');
            END IF;
        END
        $$
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM ag_catalog.ag_label
                WHERE graph = (SELECT graphid FROM ag_catalog.ag_graph WHERE name = 'sentinel_graph')
                  AND name = 'Actor'
            ) THEN
                PERFORM ag_catalog.create_vlabel('sentinel_graph', 'Actor');
            END IF;
        END
        $$
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM ag_catalog.ag_label
                WHERE graph = (SELECT graphid FROM ag_catalog.ag_graph WHERE name = 'sentinel_graph')
                  AND name = 'INTERACTED_WITH'
            ) THEN
                PERFORM ag_catalog.create_elabel('sentinel_graph', 'INTERACTED_WITH');
            END IF;
        END
        $$
        """
    )
    op.execute(
        'CREATE INDEX IF NOT EXISTS "Actor_tenant_actor_idx" '
        'ON sentinel_graph."Actor" '
        "USING btree ("
        "ag_catalog.agtype_access_operator(properties, '\"tenant_id\"'::agtype), "
        "ag_catalog.agtype_access_operator(properties, '\"actor_id\"'::agtype))"
    )
    op.execute(
        'CREATE INDEX IF NOT EXISTS "INTERACTED_WITH_tenant_idx" '
        'ON sentinel_graph."INTERACTED_WITH" '
        "USING btree (ag_catalog.agtype_access_operator(properties, '\"tenant_id\"'::agtype))"
    )
    op.execute("GRANT USAGE ON SCHEMA ag_catalog TO sentinel_app")
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA ag_catalog TO sentinel_app")
    op.execute("GRANT USAGE ON SCHEMA sentinel_graph TO sentinel_app")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA sentinel_graph TO sentinel_app"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA sentinel_graph "
        "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sentinel_app"
    )


def downgrade() -> None:
    op.execute(
        "REVOKE SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA sentinel_graph "
        "FROM sentinel_app"
    )
    op.execute("REVOKE USAGE ON SCHEMA sentinel_graph FROM sentinel_app")
    op.execute("REVOKE SELECT ON ALL TABLES IN SCHEMA ag_catalog FROM sentinel_app")
    op.execute("REVOKE USAGE ON SCHEMA ag_catalog FROM sentinel_app")
    op.execute('DROP INDEX IF EXISTS sentinel_graph."INTERACTED_WITH_tenant_idx"')
    op.execute('DROP INDEX IF EXISTS sentinel_graph."Actor_tenant_actor_idx"')
