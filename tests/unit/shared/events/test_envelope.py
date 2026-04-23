# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from shared.events import SCHEMA_VERSION, EventEnvelope, Topic
from shared.schemas import Event, EventType

pytestmark = pytest.mark.unit


def _make_event_payload() -> Event:
    return Event(
        id=uuid4(),
        tenant_id=uuid4(),
        conversation_id=uuid4(),
        actor_id=uuid4(),
        timestamp=datetime.now(UTC),
        type=EventType.MESSAGE,
        content_hash="e" * 64,
    )


def test_envelope_stamps_default_schema_version() -> None:
    payload = _make_event_payload()
    env: EventEnvelope[Event] = EventEnvelope(
        topic=Topic.EVENT_INGESTED,
        idempotency_key="tenant-xyz:evt-1",
        tenant_id=payload.tenant_id,
        published_at=datetime.now(UTC),
        payload=payload,
    )
    assert env.schema_version == SCHEMA_VERSION


def test_envelope_requires_idempotency_key() -> None:
    payload = _make_event_payload()
    with pytest.raises(ValidationError):
        EventEnvelope(
            topic=Topic.EVENT_INGESTED,
            idempotency_key="",
            tenant_id=payload.tenant_id,
            published_at=datetime.now(UTC),
            payload=payload,
        )


def test_envelope_roundtrip_with_generic_payload() -> None:
    payload = _make_event_payload()
    env: EventEnvelope[Event] = EventEnvelope(
        topic=Topic.EVENT_SCORED,
        idempotency_key=f"evt:{payload.id}",
        tenant_id=payload.tenant_id,
        published_at=datetime.now(UTC),
        trace_id="abcdef1234567890",
        payload=payload,
    )
    data = env.model_dump(mode="json")
    restored = EventEnvelope[Event].model_validate(data)
    assert restored == env
    assert restored.payload == payload


def test_all_topics_distinct() -> None:
    assert len({t.value for t in Topic}) == len(list(Topic))
