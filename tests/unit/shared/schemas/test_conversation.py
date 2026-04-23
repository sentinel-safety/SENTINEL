# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from shared.schemas import ChannelType, Conversation

pytestmark = pytest.mark.unit


def _make_conversation(**overrides: object) -> Conversation:
    now = datetime.now(UTC)
    defaults = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "participant_actor_ids": (uuid4(), uuid4()),
        "started_at": now - timedelta(minutes=5),
        "last_message_at": now,
        "channel_type": ChannelType.DM,
    }
    return Conversation.model_validate({**defaults, **overrides})


def test_conversation_requires_at_least_one_participant() -> None:
    with pytest.raises(ValidationError):
        _make_conversation(participant_actor_ids=())


def test_conversation_participants_must_be_unique() -> None:
    dup = uuid4()
    with pytest.raises(ValidationError, match="unique"):
        _make_conversation(participant_actor_ids=(dup, dup))


def test_last_message_cannot_precede_start() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValidationError, match="precede"):
        _make_conversation(
            started_at=now,
            last_message_at=now - timedelta(seconds=1),
        )


def test_valid_conversation_roundtrips() -> None:
    c = _make_conversation(channel_type=ChannelType.GROUP)
    data = c.model_dump(mode="json")
    assert Conversation.model_validate(data) == c
