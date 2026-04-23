# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncEngine

from services.dashboard_bff.app.main import create_app as create_bff
from services.scoring.app.federation_dispatch import maybe_dispatch_federation
from shared.schemas.enums import ResponseTier
from tests.integration._phase7b_helpers import (
    auth_headers,
    fast_settings,
    issue_admin_token,
    seed_tenant,
    seed_user,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_chaos_redis_unreachable_does_not_crash_federation_dispatch(
    admin_engine: AsyncEngine, clean_tables: None, caplog: pytest.LogCaptureFixture
) -> None:
    """Redis being down must not propagate exceptions out of the fire-and-forget
    federation dispatch — upstream scoring response must still succeed."""
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) VALUES (:t, 'chaos', 'free', "
                "'{}', 30, '{}'::jsonb)"
            ),
            {"t": str(tenant_id)},
        )
        await conn.execute(
            text(
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band) "
                "VALUES (:a, :t, :h, 'unknown')"
            ),
            {"a": str(actor_id), "t": str(tenant_id), "h": "c" * 64},
        )

    class _BrokenRedis:
        async def xadd(self, *a: object, **kw: object) -> str:
            raise ConnectionError("redis unreachable")

        async def aclose(self) -> None:
            return None

    caplog.set_level(logging.WARNING)
    with patch(
        "services.scoring.app.federation_dispatch.aioredis.from_url",
        return_value=_BrokenRedis(),
    ):
        maybe_dispatch_federation(
            tenant_id=tenant_id,
            actor_id=actor_id,
            new_tier=ResponseTier.CRITICAL,
            tier_threshold=int(ResponseTier.RESTRICT),
            federation_enabled=True,
            federation_publish=True,
            signal_kinds=("grooming_slow_burn",),
            flagged_at=datetime.now(UTC),
        )
        pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

    assert any(
        "federation dispatch failed" in record.message for record in caplog.records
    ), "Redis failure must be logged via warning, not raised"


async def test_chaos_postgres_unreachable_returns_clean_500_not_traceback(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    """If Postgres is down during a BFF request, the response must be a clean
    5xx — never a leaked traceback with SQL state, and never a process crash."""
    tenant_id = str(uuid.uuid4())
    await seed_tenant(admin_engine, tenant_id)
    user_id = await seed_user(admin_engine, tenant_id, role="admin")
    del user_id
    settings = fast_settings()
    token = issue_admin_token(settings=settings, tenant_id=uuid.UUID(tenant_id))
    app = create_bff(settings)

    @asynccontextmanager
    async def _boom(*a: object, **kw: object):  # type: ignore[no-untyped-def]
        raise OperationalError("SELECT 1", {}, ConnectionRefusedError("postgres down"))
        yield  # unreachable; keeps decorator typing happy

    with patch(
        "services.dashboard_bff.app.routes.alerts.tenant_session",
        new=_boom,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://t",
        ) as client:
            resp = await client.get(
                "/dashboard/api/alerts",
                headers=auth_headers(token),
            )
    assert resp.status_code >= 500, "DB outage should surface as a 5xx, not 200"
    assert (
        "OperationalError" not in resp.text
    ), "internal exception class must not leak in response body"
    assert "SELECT 1" not in resp.text, "raw SQL must not leak in response body"
