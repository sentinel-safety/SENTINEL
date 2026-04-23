"""honeypot activation log + evidence package tables with rls"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_honeypot"
down_revision: str | Sequence[str] | None = "0007_dashboard_user"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "honeypot_evidence_package",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("persona_id", sa.String(length=64), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "json_payload",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(content_hash) = 64",
            name=op.f("ck_honeypot_content_hash_len"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_honeypot_evidence_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["actor.id"],
            name=op.f("fk_honeypot_evidence_actor_id_actor"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_honeypot_evidence_package")),
    )
    op.create_index(
        "ix_honeypot_evidence_tenant_created",
        "honeypot_evidence_package",
        ["tenant_id", "created_at"],
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON honeypot_evidence_package TO sentinel_app")
    op.execute("ALTER TABLE honeypot_evidence_package ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE honeypot_evidence_package FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON honeypot_evidence_package
        USING (tenant_id::text = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))
        """
    )

    op.create_table(
        "honeypot_activation_log",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("persona_id", sa.String(length=64), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column(
            "decision_reasons",
            postgresql.ARRAY(sa.String(length=64)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("evidence_package_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "decision in ('allow','deny')",
            name=op.f("ck_honeypot_decision_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_honeypot_log_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["actor.id"],
            name=op.f("fk_honeypot_log_actor_id_actor"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_package_id"],
            ["honeypot_evidence_package.id"],
            name=op.f("fk_honeypot_log_evidence_package"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_honeypot_activation_log")),
    )
    op.create_index(
        "ix_honeypot_log_tenant_actor_activated",
        "honeypot_activation_log",
        ["tenant_id", "actor_id", "activated_at"],
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON honeypot_activation_log TO sentinel_app")
    op.execute("ALTER TABLE honeypot_activation_log ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE honeypot_activation_log FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON honeypot_activation_log
        USING (tenant_id::text = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON honeypot_activation_log")
    op.execute("ALTER TABLE honeypot_activation_log NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE honeypot_activation_log DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_honeypot_log_tenant_actor_activated", table_name="honeypot_activation_log")
    op.drop_table("honeypot_activation_log")

    op.execute("DROP POLICY IF EXISTS tenant_isolation ON honeypot_evidence_package")
    op.execute("ALTER TABLE honeypot_evidence_package NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE honeypot_evidence_package DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_honeypot_evidence_tenant_created", table_name="honeypot_evidence_package")
    op.drop_table("honeypot_evidence_package")
