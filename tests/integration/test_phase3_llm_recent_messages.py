# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.patterns.app import stream_worker
from shared.contracts.patterns import DetectRequest
from shared.contracts.preprocess import ExtractedFeatures
from shared.patterns import LLMPatternContext, PatternMatch
from shared.patterns.matches import DetectionMode
from shared.schemas.enums import EventType
from shared.schemas.event import Event
from shared.scoring.signals import SignalKind

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed(engine: AsyncEngine, tenant_id, actor_id) -> None:  # type: ignore[no-untyped-def]
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) VALUES (:t, 'acme', 'free', '{}', 30, "
                "'{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"t": str(tenant_id)},
        )
        await conn.execute(
            text(
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band, metadata) "
                "VALUES (:a, :t, :h, 'unknown', '{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"a": str(actor_id), "t": str(tenant_id), "h": "a" * 64},
        )


async def _insert_event(engine, tenant_id, actor_id, normalized, when) -> None:  # type: ignore[no-untyped-def]
    conv_id = uuid4()
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO conversation (id, tenant_id, participant_actor_ids, started_at, "
                "last_message_at, channel_type) VALUES (:c, :t, :p, :s, :l, 'dm')"
            ),
            {"c": str(conv_id), "t": str(tenant_id), "p": [str(actor_id)], "s": when, "l": when},
        )
        await conn.execute(
            text(
                "INSERT INTO event (id, tenant_id, conversation_id, actor_id, target_actor_ids, "
                "timestamp, type, content_hash, content_features, idempotency_key) "
                "VALUES (:i, :t, :c, :a, :tg, :ts, 'message', :h, CAST(:cf AS jsonb), :k)"
            ),
            {
                "i": str(uuid4()),
                "t": str(tenant_id),
                "c": str(conv_id),
                "a": str(actor_id),
                "tg": [],
                "ts": when,
                "h": "b" * 64,
                "cf": f'{{"normalized_content": "{normalized}"}}',
                "k": str(uuid4()),
            },
        )


class _CapturingPattern:
    name = "capture"
    signal_kind = SignalKind.FRIENDSHIP_FORMING
    mode = DetectionMode.LLM

    def __init__(self, sink: list[LLMPatternContext]) -> None:
        self._sink = sink

    async def detect_llm(self, ctx: LLMPatternContext) -> tuple[PatternMatch, ...]:
        self._sink.append(ctx)
        return ()


async def test_run_llm_patterns_populates_recent_messages(
    admin_engine: AsyncEngine, clean_tables: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed(admin_engine, tenant_id, actor_id)
    now = datetime.now(UTC)
    await _insert_event(
        admin_engine, tenant_id, actor_id, "lets chat more", now - timedelta(days=1)
    )
    await _insert_event(
        admin_engine, tenant_id, actor_id, "where do you live", now - timedelta(days=2)
    )

    captured: list[LLMPatternContext] = []

    def _build(_provider: object) -> tuple[_CapturingPattern, ...]:
        return (_CapturingPattern(captured),)

    monkeypatch.setattr(stream_worker, "build_llm_patterns", _build)

    event = Event(
        id=uuid4(),
        tenant_id=tenant_id,
        conversation_id=uuid4(),
        actor_id=actor_id,
        timestamp=now,
        type=EventType.MESSAGE,
        content_hash="c" * 64,
    )
    features = ExtractedFeatures(
        normalized_content="hello",
        language="en",
        token_count=1,
        contains_url=False,
        contains_contact_request=False,
        minor_recipient=True,
        late_night_local=False,
    )

    await stream_worker._run_llm_patterns(DetectRequest(event=event, features=features))

    assert len(captured) == 1
    texts = captured[0].recent_messages
    assert "lets chat more" in texts
    assert "where do you live" in texts
