# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import os
from uuid import uuid4

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.dashboard_bff.app.main import create_app
from shared.db.session import tenant_session
from shared.federation.publisher_repository import register_publisher
from tests.integration._phase7b_helpers import fast_settings, issue_admin_token

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed(engine: AsyncEngine, tenant_id: object) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                f"VALUES ('{tenant_id}', 'rep-view', 'free', '{{}}', 30, '{{}}'::jsonb)"
                " ON CONFLICT DO NOTHING"
            )
        )


async def test_list_publishers_returns_snapshots(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    publisher_id = uuid4()
    reporter_id = uuid4()
    await _seed(admin_engine, reporter_id)
    await _seed(admin_engine, publisher_id)

    async with tenant_session(publisher_id) as session:
        await register_publisher(
            session,
            tenant_id=publisher_id,
            display_name="Pub A",
            hmac_secret=os.urandom(32),
            jurisdictions=["US"],
        )

    settings = fast_settings()
    token = issue_admin_token(tenant_id=reporter_id, settings=settings)
    app = create_app(settings)
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get(
            "/dashboard/api/federation/publishers",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
    data = r.json()
    assert len(data["publishers"]) >= 1
    pub = next(p for p in data["publishers"] if p["tenant_id"] == str(publisher_id))
    assert pub["display_name"] == "Pub A"
    assert pub["reputation"] == 50
    assert "US" in pub["jurisdictions"]


async def test_report_false_signal_decrements_reputation(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    publisher_id = uuid4()
    reporter_id = uuid4()
    await _seed(admin_engine, publisher_id)
    await _seed(admin_engine, reporter_id)

    async with tenant_session(publisher_id) as session:
        await register_publisher(
            session,
            tenant_id=publisher_id,
            display_name="Pub B",
            hmac_secret=os.urandom(32),
        )

    import struct
    from datetime import UTC, datetime

    from shared.federation.signal_repository import insert_signal

    fp = tuple(float(i) / 16 for i in range(16))
    fp_bytes = struct.pack("16f", *fp)

    async with tenant_session(publisher_id) as session:
        signal_id = await insert_signal(
            session,
            publisher_tenant_id=publisher_id,
            fingerprint_bytes=fp_bytes,
            signal_kinds=("risk_assessment",),
            flagged_at=datetime.now(UTC),
            commit=os.urandom(32),
        )

    settings = fast_settings()
    token = issue_admin_token(tenant_id=reporter_id, settings=settings)
    app = create_app(settings)
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post(
            "/dashboard/api/federation/false-signal",
            json={"signal_id": str(signal_id), "reason": "false positive"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200

    async with tenant_session(publisher_id) as session:
        from sqlalchemy import select

        from shared.db.models import FederationPublisher

        pub_row = (
            await session.execute(
                select(FederationPublisher).where(FederationPublisher.tenant_id == publisher_id)
            )
        ).scalar_one()
    assert pub_row.reputation < 50
