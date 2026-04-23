# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from shared.contracts.preprocess import ExtractedFeatures
from shared.memory import ActorMemoryView
from shared.patterns import SyncPatternContext
from shared.schemas.enums import EventType
from shared.schemas.event import Event

pytestmark = pytest.mark.unit


def _event() -> Event:
    return Event(
        id=uuid4(),
        tenant_id=uuid4(),
        conversation_id=uuid4(),
        actor_id=uuid4(),
        timestamp=datetime.now(UTC),
        type=EventType.MESSAGE,
        content_hash="a" * 64,
    )


def _features() -> ExtractedFeatures:
    return ExtractedFeatures(
        normalized_content="hi",
        language="en",
        token_count=1,
        contains_url=False,
        contains_contact_request=False,
        minor_recipient=False,
        late_night_local=False,
    )


def test_sync_context_default_actor_memory_is_none() -> None:
    ctx = SyncPatternContext(event=_event(), features=_features())
    assert ctx.actor_memory is None


def test_sync_context_accepts_actor_memory() -> None:
    view = ActorMemoryView(
        distinct_conversations_last_window=2,
        distinct_minor_targets_last_window=1,
        pattern_counts_by_kind={},
        stages_observed=(),
        first_contact_at=None,
        most_recent_contact_at=None,
        total_events_last_window=2,
    )
    ctx = SyncPatternContext(event=_event(), features=_features(), actor_memory=view)
    assert ctx.actor_memory is view
