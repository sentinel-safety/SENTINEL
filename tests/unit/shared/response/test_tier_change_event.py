# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from shared.response.tier_change import TierChangeEvent
from shared.schemas.enums import ResponseTier

pytestmark = pytest.mark.unit


def test_tier_change_event_serialises_round_trip() -> None:
    now = datetime.now(UTC)
    evt = TierChangeEvent(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        event_id=uuid4(),
        previous_tier=ResponseTier.ACTIVE_MONITOR,
        new_tier=ResponseTier.RESTRICT,
        new_score=82,
        triggered_at=now,
    )
    data = evt.model_dump(mode="json")
    restored = TierChangeEvent.model_validate(data)
    assert restored == evt


def test_rejects_same_tier() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValueError):
        TierChangeEvent(
            tenant_id=uuid4(),
            actor_id=uuid4(),
            event_id=uuid4(),
            previous_tier=ResponseTier.WATCH,
            new_tier=ResponseTier.WATCH,
            new_score=30,
            triggered_at=now,
        )
