"""age sequence grants for sentinel_app"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0004_age_seqs"
down_revision: str | Sequence[str] | None = "0003_age_graph"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA ag_catalog TO sentinel_app")
    op.execute(
        "GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA sentinel_graph TO sentinel_app"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA sentinel_graph "
        "GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO sentinel_app"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA ag_catalog "
        "GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO sentinel_app"
    )


def downgrade() -> None:
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA ag_catalog "
        "REVOKE USAGE, SELECT, UPDATE ON SEQUENCES FROM sentinel_app"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA sentinel_graph "
        "REVOKE USAGE, SELECT, UPDATE ON SEQUENCES FROM sentinel_app"
    )
    op.execute(
        "REVOKE USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA sentinel_graph FROM sentinel_app"
    )
    op.execute(
        "REVOKE USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA ag_catalog FROM sentinel_app"
    )
