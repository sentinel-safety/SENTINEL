from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import httpx
import pytest
import respx
from httpx import Response

from sentinel import ResponseTier, ScoreResult, SentinelClient
from sentinel.errors import AuthError


def _make_client(base_url: str, api_key: str) -> SentinelClient:
    return SentinelClient(
        api_key=api_key,
        base_url=base_url,
        retry_attempts=3,
        retry_base_seconds=0.0,
        retry_cap_seconds=0.0,
    )


@respx.mock
def test_returns_fallback_on_repeated_500(base_url: str, api_key: str) -> None:
    respx.post(f"{base_url}/v1/events").mock(return_value=Response(503))
    client = _make_client(base_url, api_key)
    result = client.events.message(
        tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
        conversation_id=UUID("00000000-0000-0000-0000-000000000002"),
        actor_external_id_hash="a" * 64,
        content="x",
        timestamp=datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC),
    )
    assert isinstance(result, ScoreResult)
    assert result.tier is ResponseTier.TRUSTED
    assert result.current_score == 0
    assert result.reasoning is None


@respx.mock
def test_returns_fallback_on_transport_error(base_url: str, api_key: str) -> None:
    respx.post(f"{base_url}/v1/events").mock(side_effect=httpx.ConnectError("boom"))
    client = _make_client(base_url, api_key)
    result = client.events.message(
        tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
        conversation_id=UUID("00000000-0000-0000-0000-000000000002"),
        actor_external_id_hash="a" * 64,
        content="x",
        timestamp=datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC),
    )
    assert result.tier is ResponseTier.TRUSTED


@respx.mock
def test_retries_on_500_then_succeeds(base_url: str, api_key: str) -> None:
    respx.post(f"{base_url}/v1/events").mock(
        side_effect=[
            Response(500),
            Response(500),
            Response(
                200,
                json={
                    "event_id": "11111111-1111-1111-1111-111111111111",
                    "current_score": 14,
                    "previous_score": 10,
                    "delta": 4,
                    "tier": "watch",
                    "signals": [],
                },
            ),
        ]
    )
    client = _make_client(base_url, api_key)
    result = client.events.message(
        tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
        conversation_id=UUID("00000000-0000-0000-0000-000000000002"),
        actor_external_id_hash="a" * 64,
        content="x",
        timestamp=datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC),
    )
    assert result.tier is ResponseTier.WATCH
    assert result.current_score == 14


@respx.mock
def test_auth_error_does_not_retry(base_url: str, api_key: str) -> None:
    route = respx.post(f"{base_url}/v1/events").mock(return_value=Response(401))
    client = _make_client(base_url, api_key)
    with pytest.raises(AuthError):
        client.events.message(
            tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
            conversation_id=UUID("00000000-0000-0000-0000-000000000002"),
            actor_external_id_hash="a" * 64,
            content="x",
            timestamp=datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC),
        )
    assert route.call_count == 1
