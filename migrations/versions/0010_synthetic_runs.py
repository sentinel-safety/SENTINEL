"""synthetic_run and synthetic_conversation tables with rls"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_synthetic_runs"
down_revision: str | Sequence[str] | None = "0009_federation_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "synthetic_run",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("requested_by_user_id", sa.UUID(), nullable=True),
        sa.Column("seed", sa.BigInteger(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column(
            "axes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "stage_mix",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status in ('pending','running','completed','failed')",
            name=op.f("ck_synthetic_run_status_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_synthetic_run_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_user_id"],
            ["dashboard_user.id"],
            name=op.f("fk_synthetic_run_requested_by_user_id_dashboard_user"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_synthetic_run")),
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON synthetic_run TO sentinel_app")
    op.execute("ALTER TABLE synthetic_run ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE synthetic_run FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON synthetic_run
        USING (tenant_id::text = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))
        """
    )

    op.create_table(
        "synthetic_conversation",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("run_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("stage", sa.String(length=40), nullable=False),
        sa.Column(
            "demographics",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("platform", sa.String(length=40), nullable=True),
        sa.Column("communication_style", sa.String(length=40), nullable=True),
        sa.Column(
            "turns",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["synthetic_run.id"],
            name=op.f("fk_synthetic_conversation_run_id_synthetic_run"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_synthetic_conversation_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_synthetic_conversation")),
    )
    op.create_index(
        "ix_synthetic_conversation_tenant_run",
        "synthetic_conversation",
        ["tenant_id", "run_id"],
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON synthetic_conversation TO sentinel_app")
    op.execute("ALTER TABLE synthetic_conversation ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE synthetic_conversation FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON synthetic_conversation
        USING (tenant_id::text = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON synthetic_conversation")
    op.execute("ALTER TABLE synthetic_conversation NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE synthetic_conversation DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_synthetic_conversation_tenant_run", table_name="synthetic_conversation")
    op.drop_table("synthetic_conversation")

    op.execute("DROP POLICY IF EXISTS tenant_isolation ON synthetic_run")
    op.execute("ALTER TABLE synthetic_run NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE synthetic_run DISABLE ROW LEVEL SECURITY")
    op.drop_table("synthetic_run")
