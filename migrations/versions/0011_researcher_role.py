"""add researcher to dashboard_user role check constraint"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0011_researcher_role"
down_revision: str | Sequence[str] | None = "0010_synthetic_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CONSTRAINT = "ck_dashboard_user_role_valid"


def upgrade() -> None:
    op.execute(f"ALTER TABLE dashboard_user DROP CONSTRAINT {_CONSTRAINT}")
    op.execute(
        f"ALTER TABLE dashboard_user ADD CONSTRAINT {_CONSTRAINT} "
        "CHECK (role in ('admin','mod','viewer','auditor','researcher'))"
    )


def downgrade() -> None:
    op.execute(f"ALTER TABLE dashboard_user DROP CONSTRAINT {_CONSTRAINT}")
    op.execute(
        f"ALTER TABLE dashboard_user ADD CONSTRAINT {_CONSTRAINT} "
        "CHECK (role in ('admin','mod','viewer','auditor'))"
    )
