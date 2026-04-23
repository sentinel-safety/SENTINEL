# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from shared.contracts.score import ScoreResponse
from shared.schemas.enums import ResponseTier
from shared.schemas.reasoning import PrimaryDriver, Reasoning

pytestmark = pytest.mark.unit


def _reasoning() -> Reasoning:
    return Reasoning(
        actor_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        score_change=18,
        new_score=64,
        new_tier=ResponseTier.THROTTLE,
        primary_drivers=(
            PrimaryDriver(
                pattern="Platform Migration Request",
                pattern_id="platform_migration",
                confidence=0.91,
                evidence="Actor asked to move to Telegram.",
            ),
        ),
        generated_at=datetime.now(UTC),
    )


def test_reasoning_defaults_to_none() -> None:
    resp = ScoreResponse(
        current_score=64,
        previous_score=46,
        delta=18,
        tier=ResponseTier.THROTTLE,
    )
    assert resp.reasoning is None


def test_reasoning_round_trips() -> None:
    resp = ScoreResponse(
        current_score=64,
        previous_score=46,
        delta=18,
        tier=ResponseTier.THROTTLE,
        reasoning=_reasoning(),
    )
    restored = ScoreResponse.model_validate(resp.model_dump(mode="json"))
    assert restored.reasoning == resp.reasoning
