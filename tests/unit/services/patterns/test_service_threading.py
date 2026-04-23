# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from services.patterns.app.service import run_sync_patterns
from shared.contracts.patterns import DetectRequest
from shared.contracts.preprocess import ExtractedFeatures
from shared.memory import ActorMemoryView
from shared.patterns import DetectionMode, PatternMatch, SyncPatternContext
from shared.schemas.enums import EventType
from shared.schemas.event import Event
from shared.scoring.signals import SignalKind

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


class _RecordingPattern:
    name = "recorder"
    signal_kind = SignalKind.FRIENDSHIP_FORMING
    mode = DetectionMode.RULE

    def __init__(self) -> None:
        self.seen: SyncPatternContext | None = None

    async def detect_sync(self, ctx: SyncPatternContext) -> tuple[PatternMatch, ...]:
        self.seen = ctx
        return ()


def _request() -> DetectRequest:
    event = Event(
        id=uuid4(),
        tenant_id=uuid4(),
        conversation_id=uuid4(),
        actor_id=uuid4(),
        timestamp=datetime.now(UTC),
        type=EventType.MESSAGE,
        content_hash="a" * 64,
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
    return DetectRequest(event=event, features=features)


async def test_run_sync_patterns_passes_actor_memory_into_context() -> None:
    recorder = _RecordingPattern()
    view = ActorMemoryView(
        distinct_conversations_last_window=4,
        distinct_minor_targets_last_window=3,
        pattern_counts_by_kind={},
        stages_observed=(),
        first_contact_at=None,
        most_recent_contact_at=None,
        total_events_last_window=4,
    )
    await run_sync_patterns(
        _request(),
        (recorder,),
        recent_distinct_minor_target_count=3,
        actor_memory=view,
    )
    assert recorder.seen is not None
    assert recorder.seen.actor_memory is view


async def test_run_sync_patterns_defaults_actor_memory_to_none() -> None:
    recorder = _RecordingPattern()
    await run_sync_patterns(_request(), (recorder,))
    assert recorder.seen is not None
    assert recorder.seen.actor_memory is None


async def test_run_sync_patterns_threads_graph_and_neighbors() -> None:
    from services.patterns.app.service import run_sync_patterns
    from shared.contracts.patterns import DetectRequest
    from shared.contracts.preprocess import ExtractedFeatures
    from shared.fingerprint.repository import FingerprintNeighbor
    from shared.graph.views import ContactGraphView
    from shared.patterns import DetectionMode
    from shared.schemas.enums import EventType
    from shared.schemas.event import Event
    from shared.scoring.signals import SignalKind

    captured: list[SyncPatternContext] = []

    class CapturePattern:
        name = "capture"
        signal_kind = SignalKind.CROSS_SESSION_ESCALATION
        mode = DetectionMode.RULE

        async def detect_sync(self, ctx: SyncPatternContext) -> tuple[PatternMatch, ...]:
            captured.append(ctx)
            return ()

    request = DetectRequest(
        event=Event(
            id=uuid4(),
            tenant_id=uuid4(),
            conversation_id=uuid4(),
            actor_id=uuid4(),
            timestamp=datetime.now(UTC),
            type=EventType.MESSAGE,
            content_hash="e" * 64,
        ),
        features=ExtractedFeatures(
            normalized_content="hi",
            language="en",
            token_count=1,
            contains_url=False,
            contains_contact_request=False,
            minor_recipient=True,
            late_night_local=False,
        ),
    )
    view = ContactGraphView(
        distinct_contacts_total=0,
        distinct_minor_contacts_window=0,
        contact_velocity_per_day=0.0,
        age_band_distribution={},
        lookback_days=7,
    )
    neighbor = FingerprintNeighbor(
        tenant_id=request.event.tenant_id, actor_id=uuid4(), score=0.9, flagged=True
    )
    await run_sync_patterns(
        request,
        (CapturePattern(),),
        contact_graph=view,
        fingerprint_neighbors=(neighbor,),
    )
    assert captured[0].contact_graph is view
    assert captured[0].fingerprint_neighbors == (neighbor,)
