"""add bug_report table"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_bug_reports"
down_revision: str | Sequence[str] | None = "0011_researcher_role"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "bug_report"
_RLS_POLICY = "bug_report_tenant_isolation"


def upgrade() -> None:
    op.create_table(
        _TABLE,
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id",
            sa.UUID(),
            sa.ForeignKey("tenant.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("reporter_email", sa.String(320), nullable=False),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="new"),
        sa.Column(
            "received_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint(
            "severity in ('low','medium','high','critical')",
            name="ck_bug_report_severity_valid",
        ),
        sa.CheckConstraint(
            "status in ('new','triaging','accepted','rejected','resolved')",
            name="ck_bug_report_status_valid",
        ),
    )
    op.create_index(
        "ix_bug_report_tenant_received",
        _TABLE,
        ["tenant_id", "received_at"],
    )
    op.execute(f"ALTER TABLE {_TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY {_RLS_POLICY} ON {_TABLE} "
        "USING (tenant_id = current_setting('app.tenant_id', true)::uuid)"
    )


def downgrade() -> None:
    op.execute(f"DROP POLICY IF EXISTS {_RLS_POLICY} ON {_TABLE}")
    op.drop_index("ix_bug_report_tenant_received", table_name=_TABLE)
    op.drop_table(_TABLE)
