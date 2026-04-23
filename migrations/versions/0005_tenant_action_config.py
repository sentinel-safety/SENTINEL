"""tenant action config table with rls"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_action_config"
down_revision: str | Sequence[str] | None = "0004_age_seqs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenant_action_config",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False, server_default="advisory"),
        sa.Column(
            "action_overrides",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("webhook_secret_hash", sa.String(length=128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "mode in ('advisory','auto_enforce')",
            name=op.f("ck_tenant_action_config_action_mode_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_tenant_action_config_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("tenant_id", name=op.f("pk_tenant_action_config")),
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_action_config TO sentinel_app")
    op.execute("ALTER TABLE tenant_action_config ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenant_action_config FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON tenant_action_config
        USING (tenant_id::text = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON tenant_action_config")
    op.execute("ALTER TABLE tenant_action_config NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenant_action_config DISABLE ROW LEVEL SECURITY")
    op.drop_table("tenant_action_config")
