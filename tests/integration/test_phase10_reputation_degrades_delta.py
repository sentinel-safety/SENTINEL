# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from services.federation.app.qdrant_federated import FederatedNeighbor
from services.patterns.app.routes import _federation_matches
from shared.scoring.signals import SignalKind

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def _neighbor(score: float, reputation: int) -> FederatedNeighbor:
    return FederatedNeighbor(
        signal_id=uuid4(),
        publisher_tenant_id=uuid4(),
        actor_hash="aa" * 32,
        score=score,
        flagged_at=datetime.now(UTC),
        reputation=reputation,
    )


async def test_high_reputation_produces_higher_confidence() -> None:
    high_rep = _neighbor(score=1.0, reputation=80)
    low_rep = _neighbor(score=1.0, reputation=20)

    matches_high = _federation_matches(
        (high_rep,),
        threshold=0.5,
        low_reputation_threshold=30,
    )
    matches_low = _federation_matches(
        (low_rep,),
        threshold=0.5,
        low_reputation_threshold=30,
    )

    assert len(matches_high) == 1
    assert len(matches_low) == 1
    assert matches_high[0].confidence > matches_low[0].confidence


async def test_confidence_formula_reputation_weighted() -> None:
    neighbor = _neighbor(score=0.9, reputation=80)
    matches = _federation_matches(
        (neighbor,),
        threshold=0.5,
        low_reputation_threshold=30,
    )
    assert len(matches) == 1
    expected = round(0.9 * (80 / 100), 4)
    assert matches[0].confidence == expected


async def test_low_reputation_confidence_formula() -> None:
    neighbor = _neighbor(score=0.9, reputation=20)
    matches = _federation_matches(
        (neighbor,),
        threshold=0.5,
        low_reputation_threshold=30,
    )
    assert len(matches) == 1
    expected = round(0.9 * (20 / 100), 4)
    assert matches[0].confidence == expected


async def test_below_threshold_excluded() -> None:
    neighbor = _neighbor(score=0.3, reputation=80)
    matches = _federation_matches(
        (neighbor,),
        threshold=0.5,
        low_reputation_threshold=30,
    )
    assert len(matches) == 0


async def test_low_reputation_excerpt_annotated() -> None:
    neighbor = _neighbor(score=0.9, reputation=20)
    matches = _federation_matches(
        (neighbor,),
        threshold=0.5,
        low_reputation_threshold=30,
    )
    assert len(matches) == 1
    excerpt = matches[0].evidence_excerpts[0]
    assert "low-reputation" in excerpt


async def test_signal_kind_correct() -> None:
    neighbor = _neighbor(score=0.9, reputation=80)
    matches = _federation_matches(
        (neighbor,),
        threshold=0.5,
        low_reputation_threshold=30,
    )
    assert matches[0].signal_kind == SignalKind.FEDERATION_SIGNAL_MATCH
