# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from services.patterns.app.library.behavioral_fingerprint_match import (
    BehavioralFingerprintMatchPattern,
)
from shared.contracts.preprocess import ExtractedFeatures
from shared.fingerprint.repository import FingerprintNeighbor
from shared.patterns import SyncPatternContext
from shared.patterns.matches import DetectionMode
from shared.schemas.enums import EventType
from shared.schemas.event import Event
from shared.scoring.signals import SignalKind

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _ctx(neighbors: tuple[FingerprintNeighbor, ...]) -> SyncPatternContext:
    return SyncPatternContext(
        event=Event(
            id=uuid4(),
            tenant_id=uuid4(),
            conversation_id=uuid4(),
            actor_id=uuid4(),
            timestamp=datetime.now(UTC),
            type=EventType.MESSAGE,
            content_hash="c" * 64,
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
        fingerprint_neighbors=neighbors,
    )


def _neighbor(*, flagged: bool, score: float) -> FingerprintNeighbor:
    return FingerprintNeighbor(tenant_id=uuid4(), actor_id=uuid4(), score=score, flagged=flagged)


async def test_fires_when_flagged_neighbor_above_threshold() -> None:
    pattern = BehavioralFingerprintMatchPattern()
    ctx = _ctx((_neighbor(flagged=True, score=0.92),))
    matches = await pattern.detect_sync(ctx)
    assert len(matches) == 1
    assert matches[0].signal_kind is SignalKind.BEHAVIORAL_FINGERPRINT_MATCH


async def test_no_fire_when_no_neighbors() -> None:
    pattern = BehavioralFingerprintMatchPattern()
    assert await pattern.detect_sync(_ctx(())) == ()


async def test_no_fire_when_only_unflagged_neighbors() -> None:
    pattern = BehavioralFingerprintMatchPattern()
    ctx = _ctx((_neighbor(flagged=False, score=0.99),))
    assert await pattern.detect_sync(ctx) == ()


async def test_no_fire_when_flagged_neighbor_below_threshold() -> None:
    pattern = BehavioralFingerprintMatchPattern()
    ctx = _ctx((_neighbor(flagged=True, score=0.5),))
    assert await pattern.detect_sync(ctx) == ()


async def test_confidence_equals_best_flagged_neighbor_score() -> None:
    pattern = BehavioralFingerprintMatchPattern()
    ctx = _ctx(
        (
            _neighbor(flagged=True, score=0.88),
            _neighbor(flagged=True, score=0.97),
            _neighbor(flagged=False, score=0.99),
        )
    )
    match = (await pattern.detect_sync(ctx))[0]
    assert 0.96 < match.confidence <= 0.97


async def test_metadata() -> None:
    pattern = BehavioralFingerprintMatchPattern()
    assert pattern.name == "behavioral_fingerprint_match"
    assert pattern.mode is DetectionMode.RULE
