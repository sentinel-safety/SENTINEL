# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from services.patterns.app.library.multi_minor_contact import MultiMinorContactPattern
from shared.contracts.preprocess import ExtractedFeatures
from shared.graph.views import ContactGraphView
from shared.patterns import SyncPatternContext
from shared.schemas.enums import EventType
from shared.schemas.event import Event
from shared.scoring.signals import SignalKind

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _ctx(*, minors: int, minor_recipient: bool = True) -> SyncPatternContext:
    return SyncPatternContext(
        event=Event(
            id=uuid4(),
            tenant_id=uuid4(),
            conversation_id=uuid4(),
            actor_id=uuid4(),
            timestamp=datetime.now(UTC),
            type=EventType.MESSAGE,
            content_hash="b" * 64,
        ),
        features=ExtractedFeatures(
            normalized_content="hi",
            language="en",
            token_count=1,
            contains_url=False,
            contains_contact_request=False,
            minor_recipient=minor_recipient,
            late_night_local=False,
        ),
        contact_graph=ContactGraphView(
            distinct_contacts_total=minors + 1,
            distinct_minor_contacts_window=minors,
            contact_velocity_per_day=minors / 1.0,
            age_band_distribution={"under_13": minors},
            lookback_days=1,
        ),
    )


@pytest.mark.parametrize("minors", [3, 5, 10])
async def test_fires_at_or_above_threshold(minors: int) -> None:
    pattern = MultiMinorContactPattern()
    matches = await pattern.detect_sync(_ctx(minors=minors))
    assert len(matches) == 1
    assert matches[0].signal_kind is SignalKind.MULTI_MINOR_CONTACT_WINDOW
    assert matches[0].pattern_name == "multi_minor_contact"


@pytest.mark.parametrize("minors", [0, 1, 2])
async def test_no_fire_below_threshold(minors: int) -> None:
    pattern = MultiMinorContactPattern()
    assert await pattern.detect_sync(_ctx(minors=minors)) == ()


async def test_no_fire_when_graph_missing() -> None:
    pattern = MultiMinorContactPattern()
    ctx = SyncPatternContext(
        event=Event(
            id=uuid4(),
            tenant_id=uuid4(),
            conversation_id=uuid4(),
            actor_id=uuid4(),
            timestamp=datetime.now(UTC),
            type=EventType.MESSAGE,
            content_hash="b" * 64,
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
    assert await pattern.detect_sync(ctx) == ()


async def test_confidence_scales_with_minor_count() -> None:
    pattern = MultiMinorContactPattern()
    low = (await pattern.detect_sync(_ctx(minors=3)))[0]
    high = (await pattern.detect_sync(_ctx(minors=10)))[0]
    assert high.confidence > low.confidence
    assert high.confidence <= 0.95
