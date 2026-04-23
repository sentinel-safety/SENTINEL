# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from shared.schemas import Event, EventType

pytestmark = pytest.mark.unit


def _make_event(**overrides: object) -> Event:
    defaults = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "conversation_id": uuid4(),
        "actor_id": uuid4(),
        "timestamp": datetime.now(UTC),
        "type": EventType.MESSAGE,
        "content_hash": "d" * 64,
    }
    return Event.model_validate({**defaults, **overrides})


def test_event_defaults_are_empty() -> None:
    e = _make_event()
    assert e.target_actor_ids == ()
    assert e.content_features == {}
    assert e.pattern_match_ids == ()
    assert e.score_delta == 0
    assert e.processed_at is None


def test_content_hash_must_be_lowercase_hex_64() -> None:
    with pytest.raises(ValidationError):
        _make_event(content_hash="Z" * 64)
    with pytest.raises(ValidationError):
        _make_event(content_hash="aa")


def test_event_roundtrip() -> None:
    e = _make_event(
        type=EventType.FRIEND_REQUEST,
        target_actor_ids=(uuid4(),),
        score_delta=+12,
        content_features={"length": 42, "language": "en"},
    )
    restored = Event.model_validate(e.model_dump(mode="json"))
    assert restored == e
