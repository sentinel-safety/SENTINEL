# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from shared.schemas import PrimaryDriver, Reasoning, ResponseTier

pytestmark = pytest.mark.unit


def test_reasoning_drives_are_bounded_confidence() -> None:
    with pytest.raises(ValidationError):
        PrimaryDriver(
            pattern="X",
            pattern_id="x",
            confidence=1.5,
            evidence="z",
        )


def test_reasoning_matches_spec_example() -> None:
    r = Reasoning(
        actor_id=uuid4(),
        tenant_id=uuid4(),
        score_change=18,
        new_score=64,
        new_tier=ResponseTier.THROTTLE,
        primary_drivers=(
            PrimaryDriver(
                pattern="Platform Migration Request",
                pattern_id="platform_migration_request",
                confidence=0.91,
                evidence="Actor asked target (claimed age 14) to move to Telegram three times.",
            ),
        ),
        context="Actor has interacted with 7 distinct minor accounts in past 14 days.",
        recommended_action_summary=(
            "Escalate to tier 3: throttle DMs to minors, require human review."
        ),
        generated_at=datetime.now(UTC),
    )
    restored = Reasoning.model_validate(r.model_dump(mode="json"))
    assert restored == r
    assert restored.new_tier == ResponseTier.THROTTLE
    assert restored.primary_drivers[0].confidence == pytest.approx(0.91)
