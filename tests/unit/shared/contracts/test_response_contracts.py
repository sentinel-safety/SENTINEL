# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from shared.contracts.response import (
    DeadLetterEntry,
    DeadLetterListResponse,
    EvaluateResponseRequest,
    EvaluateResponseResponse,
)
from shared.response.tier_change import TierChangeEvent
from shared.schemas.enums import ResponseTier

pytestmark = pytest.mark.unit


def _tier_change() -> TierChangeEvent:
    return TierChangeEvent(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        event_id=uuid4(),
        previous_tier=ResponseTier.WATCH,
        new_tier=ResponseTier.ACTIVE_MONITOR,
        new_score=45,
        triggered_at=datetime.now(UTC),
    )


def test_evaluate_request_round_trip() -> None:
    req = EvaluateResponseRequest(tier_change=_tier_change())
    data = req.model_dump(mode="json")
    restored = EvaluateResponseRequest.model_validate(data)
    assert restored == req


def test_evaluate_response_holds_action_kinds() -> None:
    resp = EvaluateResponseResponse(enqueued=True, recommended_action_kinds=("silent_log",))
    assert resp.recommended_action_kinds == ("silent_log",)


def test_dead_letter_list() -> None:
    entry = DeadLetterEntry(
        entry_id="1-0",
        tenant_id=uuid4(),
        actor_id=uuid4(),
        event_kind="tier.changed",
        attempt=5,
        reason="retries_exhausted",
        enqueued_at=datetime.now(UTC),
    )
    lst = DeadLetterListResponse(entries=(entry,))
    assert lst.entries[0].reason == "retries_exhausted"
