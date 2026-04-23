# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine

from shared.db.models import BugReport
from shared.db.session import tenant_session

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_TENANT_SQL = text(
    "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, data_retention_days, feature_flags) "
    "VALUES (:t, 'test', 'free', '{}', 30, '{}'::jsonb)"
)


async def test_tenant_cannot_read_other_tenants_bug_report(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    tenant_a = uuid4()
    tenant_b = uuid4()
    async with admin_engine.begin() as conn:
        await conn.execute(_TENANT_SQL, {"t": str(tenant_a)})
        await conn.execute(_TENANT_SQL, {"t": str(tenant_b)})

    async with tenant_session(tenant_a) as s:
        s.add(
            BugReport(
                tenant_id=tenant_a,
                reporter_email="researcher@example.com",
                summary="XSS in dashboard",
                details="Found an XSS vulnerability via the search input field.",
                severity="high",
            )
        )

    async with tenant_session(tenant_b) as s:
        rows = (await s.execute(select(BugReport))).scalars().all()

    assert rows == []
