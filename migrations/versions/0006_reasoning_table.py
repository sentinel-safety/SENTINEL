"""reasoning table with rls"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_reasoning"
down_revision: str | Sequence[str] | None = "0005_action_config"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reasoning",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=True),
        sa.Column(
            "reasoning_json",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_reasoning_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["actor.id"],
            name=op.f("fk_reasoning_actor_id_actor"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["event.id"],
            name=op.f("fk_reasoning_event_id_event"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reasoning")),
    )
    op.create_index(
        "ix_reasoning_tenant_actor_created",
        "reasoning",
        ["tenant_id", "actor_id", "created_at"],
    )
    op.create_index(
        "ix_reasoning_tenant_event",
        "reasoning",
        ["tenant_id", "event_id"],
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON reasoning TO sentinel_app")
    op.execute("ALTER TABLE reasoning ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reasoning FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON reasoning
        USING (tenant_id::text = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON reasoning")
    op.execute("ALTER TABLE reasoning NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reasoning DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_reasoning_tenant_event", table_name="reasoning")
    op.drop_index("ix_reasoning_tenant_actor_created", table_name="reasoning")
    op.drop_table("reasoning")
