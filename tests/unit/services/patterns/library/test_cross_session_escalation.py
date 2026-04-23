# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from services.patterns.app.library.cross_session_escalation import (
    CrossSessionEscalationPattern,
)
from shared.contracts.preprocess import ExtractedFeatures
from shared.memory import ActorMemoryView
from shared.patterns import SyncPatternContext
from shared.schemas.enums import EventType
from shared.schemas.event import Event
from shared.scoring.signals import SignalKind

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _features(minor: bool) -> ExtractedFeatures:
    return ExtractedFeatures(
        normalized_content="hey",
        language="en",
        token_count=1,
        contains_url=False,
        contains_contact_request=False,
        minor_recipient=minor,
        late_night_local=False,
    )


def _event() -> Event:
    return Event(
        id=uuid4(),
        tenant_id=uuid4(),
        conversation_id=uuid4(),
        actor_id=uuid4(),
        timestamp=datetime.now(UTC),
        type=EventType.MESSAGE,
        content_hash="4" * 64,
    )


def _view(convs: int, targets: int) -> ActorMemoryView:
    return ActorMemoryView(
        distinct_conversations_last_window=convs,
        distinct_minor_targets_last_window=targets,
        pattern_counts_by_kind={},
        stages_observed=(),
        first_contact_at=None,
        most_recent_contact_at=None,
        total_events_last_window=convs,
    )


async def test_fires_when_three_conversations_two_targets_to_minor() -> None:
    pattern = CrossSessionEscalationPattern()
    ctx = SyncPatternContext(event=_event(), features=_features(True), actor_memory=_view(3, 2))
    matches = await pattern.detect_sync(ctx)
    assert len(matches) == 1
    match = matches[0]
    assert match.signal_kind is SignalKind.CROSS_SESSION_ESCALATION
    assert 0.4 <= match.confidence <= 0.9
    assert any("3" in e or "conversations" in e for e in match.evidence_excerpts)


async def test_confidence_scales_with_conversation_count() -> None:
    pattern = CrossSessionEscalationPattern()
    ctx_low = SyncPatternContext(event=_event(), features=_features(True), actor_memory=_view(3, 2))
    ctx_high = SyncPatternContext(
        event=_event(), features=_features(True), actor_memory=_view(10, 5)
    )
    low = (await pattern.detect_sync(ctx_low))[0]
    high = (await pattern.detect_sync(ctx_high))[0]
    assert high.confidence > low.confidence
    assert high.confidence <= 0.9


async def test_does_not_fire_when_memory_missing() -> None:
    pattern = CrossSessionEscalationPattern()
    ctx = SyncPatternContext(event=_event(), features=_features(True), actor_memory=None)
    assert await pattern.detect_sync(ctx) == ()


async def test_does_not_fire_when_recipient_not_minor() -> None:
    pattern = CrossSessionEscalationPattern()
    ctx = SyncPatternContext(event=_event(), features=_features(False), actor_memory=_view(3, 2))
    assert await pattern.detect_sync(ctx) == ()


async def test_does_not_fire_below_conversation_threshold() -> None:
    pattern = CrossSessionEscalationPattern()
    ctx = SyncPatternContext(event=_event(), features=_features(True), actor_memory=_view(2, 2))
    assert await pattern.detect_sync(ctx) == ()


async def test_does_not_fire_below_target_threshold() -> None:
    pattern = CrossSessionEscalationPattern()
    ctx = SyncPatternContext(event=_event(), features=_features(True), actor_memory=_view(3, 1))
    assert await pattern.detect_sync(ctx) == ()
