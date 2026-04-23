# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.scoring.app.federation_dispatch import maybe_dispatch_federation
from shared.schemas.enums import ResponseTier

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed_tenant(
    engine: AsyncEngine,
    tenant_id: object,
    *,
    federation_enabled: bool = True,
    federation_publish: bool = True,
) -> None:
    import json

    flags = json.dumps(
        {
            "federation_enabled": federation_enabled,
            "federation_publish": federation_publish,
        }
    )
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                f"VALUES ('{tenant_id}', 'fed-score', 'free', '{{}}', 30, "
                f"'{flags}'::jsonb) ON CONFLICT DO NOTHING"
            ),
        )


async def test_fires_when_flags_set_and_tier_reached(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed_tenant(admin_engine, tenant_id)

    published: list[object] = []

    async def _fake_publish(**kwargs: object) -> None:
        published.append(kwargs)

    with patch(
        "services.scoring.app.federation_dispatch._publish",
        new=AsyncMock(side_effect=_fake_publish),
    ):
        import asyncio

        tasks_before = set(asyncio.all_tasks())
        maybe_dispatch_federation(
            tenant_id=tenant_id,
            actor_id=actor_id,
            new_tier=ResponseTier.RESTRICT,
            tier_threshold=ResponseTier.RESTRICT,
            federation_enabled=True,
            federation_publish=True,
            signal_kinds=("risk_assessment",),
            flagged_at=datetime.now(UTC),
        )
        new_tasks = asyncio.all_tasks() - tasks_before
        if new_tasks:
            await asyncio.gather(*new_tasks, return_exceptions=True)

    assert len(published) == 1


async def test_does_not_fire_below_threshold() -> None:
    called = AsyncMock()
    with patch("services.scoring.app.federation_dispatch._publish", called):
        maybe_dispatch_federation(
            tenant_id=uuid4(),
            actor_id=uuid4(),
            new_tier=ResponseTier.THROTTLE,
            tier_threshold=ResponseTier.RESTRICT,
            federation_enabled=True,
            federation_publish=True,
            signal_kinds=("risk_assessment",),
            flagged_at=datetime.now(UTC),
        )
        import asyncio

        await asyncio.sleep(0)

    called.assert_not_awaited()


async def test_does_not_fire_when_federation_disabled() -> None:
    called = AsyncMock()
    with patch("services.scoring.app.federation_dispatch._publish", called):
        maybe_dispatch_federation(
            tenant_id=uuid4(),
            actor_id=uuid4(),
            new_tier=ResponseTier.RESTRICT,
            tier_threshold=ResponseTier.RESTRICT,
            federation_enabled=False,
            federation_publish=True,
            signal_kinds=("risk_assessment",),
            flagged_at=datetime.now(UTC),
        )
        import asyncio

        await asyncio.sleep(0)

    called.assert_not_awaited()


async def test_does_not_fire_when_publish_disabled() -> None:
    called = AsyncMock()
    with patch("services.scoring.app.federation_dispatch._publish", called):
        maybe_dispatch_federation(
            tenant_id=uuid4(),
            actor_id=uuid4(),
            new_tier=ResponseTier.RESTRICT,
            tier_threshold=ResponseTier.RESTRICT,
            federation_enabled=True,
            federation_publish=False,
            signal_kinds=("risk_assessment",),
            flagged_at=datetime.now(UTC),
        )
        import asyncio

        await asyncio.sleep(0)

    called.assert_not_awaited()
