# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

import fakeredis.aioredis as fakeredis
import pytest
import respx
from httpx import Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.response.app.webhook_worker import run_webhook_worker
from shared.response.mandatory_report import evaluate_mandatory_report
from shared.schemas.enums import Jurisdiction, ResponseTier
from shared.scoring.signals import ScoreSignal, SignalKind

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_URL = "https://regulator.example/hook"


async def _seed(admin_engine: AsyncEngine, tid: str) -> None:
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) VALUES (:t, 'acme', 'free', ARRAY['US'], 30, '{}'::jsonb)"
            ),
            {"t": tid},
        )
        await conn.execute(
            text(
                "INSERT INTO webhook_endpoint (id, tenant_id, url, secret_hash, "
                "subscribed_topics, active) VALUES (:id, :t, :u, :sh, "
                "ARRAY['tier.changed','mandatory_report.required'], true)"
            ),
            {"id": str(uuid4()), "t": tid, "u": _URL, "sh": "a" * 64},
        )
        await conn.execute(
            text(
                "INSERT INTO tenant_action_config (tenant_id, mode, action_overrides, "
                "webhook_secret_hash) VALUES (:t, 'auto_enforce', '{}'::jsonb, :s)"
            ),
            {"t": tid, "s": "a" * 64},
        )


async def test_us_critical_with_sexual_escalation_emits_mandatory_report(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid4())
    await _seed(admin_engine, tid)
    pkg = evaluate_mandatory_report(
        tenant_id=UUID(tid),
        actor_id=uuid4(),
        tier=ResponseTier.CRITICAL,
        jurisdictions=(Jurisdiction.US,),
        signals=(ScoreSignal(kind=SignalKind.SEXUAL_ESCALATION, confidence=1.0),),
    )
    assert pkg is not None
    assert pkg.report_template == "NCMEC_CYBERTIPLINE"


async def test_critical_below_triggering_signals_does_not_emit(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid4())
    await _seed(admin_engine, tid)
    pkg = evaluate_mandatory_report(
        tenant_id=UUID(tid),
        actor_id=uuid4(),
        tier=ResponseTier.CRITICAL,
        jurisdictions=(Jurisdiction.US,),
        signals=(ScoreSignal(kind=SignalKind.FRIENDSHIP_FORMING, confidence=1.0),),
    )
    assert pkg is None


async def test_mandatory_report_webhook_delivery_shape(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid4())
    await _seed(admin_engine, tid)
    from services.response.app.stream_producer import enqueue_tier_change
    from shared.response.tier_change import TierChangeEvent

    redis = fakeredis.FakeRedis(decode_responses=False)
    event = TierChangeEvent(
        tenant_id=UUID(tid),
        actor_id=uuid4(),
        event_id=uuid4(),
        previous_tier=ResponseTier.RESTRICT,
        new_tier=ResponseTier.CRITICAL,
        new_score=95,
        triggered_at=datetime.now(UTC),
    )
    await enqueue_tier_change(redis, stream_name="response:tier_changes", event=event)
    stop = asyncio.Event()
    with respx.mock() as mock:
        route = mock.post(_URL).mock(return_value=Response(200))
        await run_webhook_worker(redis, stop_event=stop, iteration_limit=1)
    assert route.called
