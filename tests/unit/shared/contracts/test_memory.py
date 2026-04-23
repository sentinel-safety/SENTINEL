# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from shared.contracts.memory import MemoryLookupRequest, MemoryLookupResponse
from shared.memory import ActorMemoryView

pytestmark = pytest.mark.unit


def test_memory_lookup_request_defaults_to_21_days() -> None:
    req = MemoryLookupRequest(tenant_id=uuid4(), actor_id=uuid4())
    assert req.lookback_days == 21


def test_memory_lookup_request_rejects_zero_days() -> None:
    with pytest.raises(ValidationError):
        MemoryLookupRequest(tenant_id=uuid4(), actor_id=uuid4(), lookback_days=0)


def test_memory_lookup_request_rejects_over_365_days() -> None:
    with pytest.raises(ValidationError):
        MemoryLookupRequest(tenant_id=uuid4(), actor_id=uuid4(), lookback_days=366)


def test_memory_lookup_response_round_trip() -> None:
    view = ActorMemoryView(
        distinct_conversations_last_window=3,
        distinct_minor_targets_last_window=2,
        pattern_counts_by_kind={},
        stages_observed=(),
        first_contact_at=None,
        most_recent_contact_at=None,
        total_events_last_window=5,
    )
    resp = MemoryLookupResponse(view=view)
    raw = resp.model_dump(mode="json")
    rebuilt = MemoryLookupResponse.model_validate(raw)
    assert rebuilt.view.distinct_conversations_last_window == 3
