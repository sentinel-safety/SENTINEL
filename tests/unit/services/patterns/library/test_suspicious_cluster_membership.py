# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from services.patterns.app.library.suspicious_cluster_membership import (
    SuspiciousClusterMembershipPattern,
)
from shared.contracts.preprocess import ExtractedFeatures
from shared.fingerprint.repository import FingerprintNeighbor
from shared.patterns import SyncPatternContext
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
            content_hash="d" * 64,
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


def _n(flagged: bool, score: float) -> FingerprintNeighbor:
    return FingerprintNeighbor(tenant_id=uuid4(), actor_id=uuid4(), score=score, flagged=flagged)


async def test_fires_when_two_flagged_neighbors_above_threshold() -> None:
    pattern = SuspiciousClusterMembershipPattern()
    ctx = _ctx((_n(True, 0.9), _n(True, 0.88), _n(False, 0.95)))
    matches = await pattern.detect_sync(ctx)
    assert len(matches) == 1
    assert matches[0].signal_kind is SignalKind.SUSPICIOUS_CLUSTER_MEMBERSHIP


async def test_no_fire_when_only_one_flagged_neighbor() -> None:
    pattern = SuspiciousClusterMembershipPattern()
    assert await pattern.detect_sync(_ctx((_n(True, 0.9),))) == ()


async def test_no_fire_when_flagged_neighbors_below_threshold() -> None:
    pattern = SuspiciousClusterMembershipPattern()
    assert await pattern.detect_sync(_ctx((_n(True, 0.5), _n(True, 0.4)))) == ()


async def test_no_fire_when_no_neighbors() -> None:
    pattern = SuspiciousClusterMembershipPattern()
    assert await pattern.detect_sync(_ctx(())) == ()


async def test_confidence_scales_with_flagged_count() -> None:
    pattern = SuspiciousClusterMembershipPattern()
    a = (await pattern.detect_sync(_ctx((_n(True, 0.9), _n(True, 0.88)))))[0]
    b = (
        await pattern.detect_sync(
            _ctx((_n(True, 0.9), _n(True, 0.92), _n(True, 0.88), _n(True, 0.86)))
        )
    )[0]
    assert b.confidence > a.confidence
    assert b.confidence <= 0.95
