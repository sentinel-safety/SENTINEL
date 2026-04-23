from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
import respx
from httpx import Response

from sentinel import EventType, ResponseTier, ScoreResult, SentinelClient


@respx.mock
def test_events_message_happy_path(base_url: str, api_key: str) -> None:
    route = respx.post(f"{base_url}/v1/events").mock(
        return_value=Response(
            200,
            json={
                "event_id": "11111111-1111-1111-1111-111111111111",
                "current_score": 24,
                "previous_score": 12,
                "delta": 12,
                "tier": "watch",
                "signals": [],
            },
        )
    )
    client = SentinelClient(api_key=api_key, base_url=base_url)
    result = client.events.message(
        tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
        conversation_id=UUID("00000000-0000-0000-0000-000000000002"),
        actor_external_id_hash="a" * 64,
        content="hi",
        timestamp=datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC),
    )
    assert isinstance(result, ScoreResult)
    assert result.tier is ResponseTier.WATCH
    assert result.current_score == 24
    assert route.called
    sent = route.calls.last.request
    assert sent.headers["authorization"] == f"Bearer {api_key}"
    body = sent.content.decode().replace(" ", "")
    assert '"event_type":"message"' in body
    assert '"actor_external_id_hash":"' + "a" * 64 + '"' in body


@respx.mock
def test_events_message_rejects_bad_hash(base_url: str, api_key: str) -> None:
    client = SentinelClient(api_key=api_key, base_url=base_url)
    with pytest.raises(ValueError):
        client.events.message(
            tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
            conversation_id=UUID("00000000-0000-0000-0000-000000000002"),
            actor_external_id_hash="not-hex",
            content="hi",
            timestamp=datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC),
        )


@respx.mock
def test_events_message_generates_idempotency_key(base_url: str, api_key: str) -> None:
    route = respx.post(f"{base_url}/v1/events").mock(
        return_value=Response(
            200,
            json={
                "event_id": "11111111-1111-1111-1111-111111111111",
                "current_score": 0,
                "previous_score": 0,
                "delta": 0,
                "tier": "trusted",
                "signals": [],
            },
        )
    )
    client = SentinelClient(api_key=api_key, base_url=base_url)
    for _ in range(2):
        client.events.message(
            tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
            conversation_id=UUID("00000000-0000-0000-0000-000000000002"),
            actor_external_id_hash="a" * 64,
            content="hi",
            timestamp=datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC),
        )
    keys = [c.request.content.decode() for c in route.calls]
    assert len(keys) == 2
    assert keys[0] != keys[1]


@respx.mock
def test_events_message_accepts_explicit_idempotency_key(base_url: str, api_key: str) -> None:
    route = respx.post(f"{base_url}/v1/events").mock(
        return_value=Response(
            200,
            json={
                "event_id": "11111111-1111-1111-1111-111111111111",
                "current_score": 0,
                "previous_score": 0,
                "delta": 0,
                "tier": "trusted",
                "signals": [],
            },
        )
    )
    client = SentinelClient(api_key=api_key, base_url=base_url)
    client.events.message(
        tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
        conversation_id=UUID("00000000-0000-0000-0000-000000000002"),
        actor_external_id_hash="a" * 64,
        content="hi",
        timestamp=datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC),
        idempotency_key="client-provided-abc",
    )
    body = route.calls.last.request.content.decode().replace(" ", "")
    assert '"idempotency_key":"client-provided-abc"' in body


@respx.mock
def test_events_message_accepts_event_type_enum(base_url: str, api_key: str) -> None:
    route = respx.post(f"{base_url}/v1/events").mock(
        return_value=Response(
            200,
            json={
                "event_id": "11111111-1111-1111-1111-111111111111",
                "current_score": 0,
                "previous_score": 0,
                "delta": 0,
                "tier": "trusted",
                "signals": [],
            },
        )
    )
    client = SentinelClient(api_key=api_key, base_url=base_url)
    client.events.message(
        tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
        conversation_id=UUID("00000000-0000-0000-0000-000000000002"),
        actor_external_id_hash="a" * 64,
        content="[image]",
        timestamp=datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC),
        event_type=EventType.IMAGE,
    )
    body = route.calls.last.request.content.decode().replace(" ", "")
    assert '"event_type":"image"' in body
