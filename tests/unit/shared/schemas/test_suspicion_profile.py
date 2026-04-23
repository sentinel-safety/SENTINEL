# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from shared.schemas import (
    ResponseTier,
    ScoreHistoryEntry,
    SuspicionProfile,
)

pytestmark = pytest.mark.unit


def _make_profile(**overrides: object) -> SuspicionProfile:
    now = datetime.now(UTC)
    defaults = {
        "actor_id": uuid4(),
        "tenant_id": uuid4(),
        "current_score": 5,
        "tier": ResponseTier.TRUSTED,
        "tier_entered_at": now,
        "last_updated": now,
    }
    return SuspicionProfile.model_validate({**defaults, **overrides})


def test_score_must_be_in_range() -> None:
    with pytest.raises(ValidationError):
        _make_profile(current_score=-1)
    with pytest.raises(ValidationError):
        _make_profile(current_score=101)


def test_profile_roundtrip_with_history() -> None:
    event_id = uuid4()
    now = datetime.now(UTC)
    history = (
        ScoreHistoryEntry(
            at=now,
            delta=+15,
            cause="pattern:platform_migration_request",
            new_score=20,
            source_event_id=event_id,
        ),
    )
    p = _make_profile(current_score=20, tier=ResponseTier.WATCH, score_history=history)
    restored = SuspicionProfile.model_validate(p.model_dump(mode="json"))
    assert restored == p
    assert restored.score_history[0].delta == 15


def test_score_history_entry_new_score_bounded() -> None:
    with pytest.raises(ValidationError):
        ScoreHistoryEntry(
            at=datetime.now(UTC),
            delta=+200,
            cause="x",
            new_score=200,
        )
