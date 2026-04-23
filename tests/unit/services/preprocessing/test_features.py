# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from services.preprocessing.app.features import (
    extract_features,
    normalize,
)
from shared.schemas.enums import AgeBand, EventType
from shared.schemas.event import Event

pytestmark = pytest.mark.unit


def _event(timestamp: datetime | None = None) -> Event:
    return Event(
        id=uuid4(),
        tenant_id=uuid4(),
        conversation_id=uuid4(),
        actor_id=uuid4(),
        target_actor_ids=(uuid4(),),
        timestamp=timestamp or datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        type=EventType.MESSAGE,
        content_hash="a" * 64,
    )


def test_normalize_lowercases_and_collapses_whitespace() -> None:
    assert normalize("  Hello   THERE  \n friend ") == "hello there friend"


def test_normalize_preserves_punctuation_for_pattern_rules() -> None:
    assert normalize("Don't TELL anyone!") == "don't tell anyone!"


def test_extract_detects_url() -> None:
    features = extract_features(
        event=_event(),
        content="check this https://discord.gg/abc",
        recipient_age_bands=(AgeBand.ADULT,),
        recipient_timezone="UTC",
    )
    assert features.contains_url is True


def test_extract_detects_contact_request() -> None:
    features = extract_features(
        event=_event(),
        content="what's your phone number?",
        recipient_age_bands=(AgeBand.BAND_13_15,),
        recipient_timezone="UTC",
    )
    assert features.contains_contact_request is True


def test_extract_flags_minor_recipient() -> None:
    features = extract_features(
        event=_event(),
        content="hi",
        recipient_age_bands=(AgeBand.UNDER_13,),
        recipient_timezone="UTC",
    )
    assert features.minor_recipient is True


def test_extract_late_night_uses_recipient_timezone() -> None:
    event = _event(timestamp=datetime(2026, 1, 1, 3, 0, tzinfo=UTC))
    features = extract_features(
        event=event,
        content="you up?",
        recipient_age_bands=(AgeBand.BAND_13_15,),
        recipient_timezone="Europe/London",
    )
    assert features.late_night_local is True


def test_extract_daytime_is_not_flagged() -> None:
    event = _event(timestamp=datetime(2026, 1, 1, 15, 0, tzinfo=UTC))
    features = extract_features(
        event=event,
        content="hello",
        recipient_age_bands=(AgeBand.BAND_13_15,),
        recipient_timezone="Europe/London",
    )
    assert features.late_night_local is False


def test_extract_token_count_and_language_default() -> None:
    features = extract_features(
        event=_event(),
        content="one two three",
        recipient_age_bands=(AgeBand.ADULT,),
        recipient_timezone="UTC",
    )
    assert features.token_count == 3
    assert features.language in {"en", "unknown"}


def test_normalize_idempotent() -> None:
    once = normalize("  hello   WORLD ")
    twice = normalize(once)
    assert once == twice
