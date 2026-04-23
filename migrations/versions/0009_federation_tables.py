"""federation publisher, signal, reputation_event, and tenant_secret tables"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_federation_tables"
down_revision: str | Sequence[str] | None = "0008_honeypot"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "federation_tenant_secret",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("hmac_secret", postgresql.BYTEA(), nullable=False),
        sa.Column("actor_pepper", postgresql.BYTEA(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_federation_tenant_secret_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("tenant_id", name=op.f("pk_federation_tenant_secret")),
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON federation_tenant_secret TO sentinel_app")
    op.execute("ALTER TABLE federation_tenant_secret ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE federation_tenant_secret FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON federation_tenant_secret
        USING (tenant_id::text = current_setting('app.tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))
        """
    )

    op.create_table(
        "federation_publisher",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column(
            "jurisdictions",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("reputation", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("hmac_secret", postgresql.BYTEA(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_federation_publisher_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("tenant_id", name=op.f("pk_federation_publisher")),
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON federation_publisher TO sentinel_app")

    op.create_table(
        "federation_signal",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("publisher_tenant_id", sa.UUID(), nullable=False),
        sa.Column("fingerprint", postgresql.BYTEA(), nullable=False),
        sa.Column(
            "signal_kinds",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
        ),
        sa.Column("flagged_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("commit", postgresql.BYTEA(), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["publisher_tenant_id"],
            ["federation_publisher.tenant_id"],
            name=op.f("fk_federation_signal_publisher_tenant_id_federation_publisher"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_federation_signal")),
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON federation_signal TO sentinel_app")

    op.create_table(
        "federation_reputation_event",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("publisher_tenant_id", sa.UUID(), nullable=False),
        sa.Column("reporter_tenant_id", sa.UUID(), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["publisher_tenant_id"],
            ["federation_publisher.tenant_id"],
            name=op.f("fk_federation_reputation_event_publisher_tenant_id_federation_publisher"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reporter_tenant_id"],
            ["tenant.id"],
            name=op.f("fk_federation_reputation_event_reporter_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_federation_reputation_event")),
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON federation_reputation_event TO sentinel_app"
    )


def downgrade() -> None:
    op.drop_table("federation_reputation_event")
    op.drop_table("federation_signal")
    op.drop_table("federation_publisher")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON federation_tenant_secret")
    op.execute("ALTER TABLE federation_tenant_secret NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE federation_tenant_secret DISABLE ROW LEVEL SECURITY")
    op.drop_table("federation_tenant_secret")
