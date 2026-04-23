"""dashboard user table with rls"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_dashboard_user"
down_revision: str | Sequence[str] | None = "0006_reasoning"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dashboard_user",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
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
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "role in ('admin','mod','viewer','auditor')",
            name=op.f("ck_dashboard_user_role_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_dashboard_user_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dashboard_user")),
        sa.UniqueConstraint("tenant_id", "email", name=op.f("uq_dashboard_user_tenant_id_email")),
    )
    op.create_index("ix_dashboard_user_tenant_id", "dashboard_user", ["tenant_id"])
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON dashboard_user TO sentinel_app")
    op.execute("ALTER TABLE dashboard_user ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE dashboard_user FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON dashboard_user
        USING (tenant_id::text = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON dashboard_user")
    op.execute("ALTER TABLE dashboard_user NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE dashboard_user DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_dashboard_user_tenant_id", table_name="dashboard_user")
    op.drop_table("dashboard_user")
