# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import json

import pytest
from pytest_httpx import HTTPXMock

from shared.llm.anthropic_provider import _API_URL, AnthropicProvider
from shared.llm.provider import LLMCallError, LLMValidationError

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

_KEY = "sk-ant-test-key"  # pragma: allowlist secret
_SCHEMA = {
    "type": "object",
    "required": ["confidence"],
    "properties": {"confidence": {"type": "number"}},
}


def _anthropic_response(payload: dict[str, object]) -> dict[str, object]:
    return {
        "id": "msg_01",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": json.dumps(payload)}],
        "model": "claude-3-5-haiku-20241022",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 10, "output_tokens": 10},
    }


async def test_returns_valid_payload(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=_API_URL,
        json=_anthropic_response({"confidence": 0.9}),
    )
    provider = AnthropicProvider(_KEY, timeout_seconds=5.0, max_attempts=1)
    result = await provider.complete(prompt="test", schema=_SCHEMA)
    assert result["confidence"] == pytest.approx(0.9)


async def test_raises_on_http_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=_API_URL, status_code=500, text="server error")
    provider = AnthropicProvider(_KEY, timeout_seconds=5.0, max_attempts=1)
    with pytest.raises(LLMCallError, match="500"):
        await provider.complete(prompt="test", schema=_SCHEMA)


async def test_raises_on_non_json_response(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=_API_URL,
        json={
            "id": "msg_01",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "not json at all"}],
            "model": "claude-3-5-haiku-20241022",
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 10, "output_tokens": 10},
        },
    )
    provider = AnthropicProvider(_KEY, timeout_seconds=5.0, max_attempts=1)
    with pytest.raises(LLMCallError, match="non-json"):
        await provider.complete(prompt="test", schema=_SCHEMA)


async def test_raises_validation_error_on_schema_mismatch(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=_API_URL,
        json=_anthropic_response({"confidence": "not-a-number"}),
    )
    provider = AnthropicProvider(_KEY, timeout_seconds=5.0, max_attempts=1)
    with pytest.raises(LLMValidationError):
        await provider.complete(prompt="test", schema=_SCHEMA)


async def test_retries_on_server_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=_API_URL, status_code=500, text="error")
    httpx_mock.add_response(
        url=_API_URL,
        json=_anthropic_response({"confidence": 0.7}),
    )
    provider = AnthropicProvider(_KEY, timeout_seconds=5.0, max_attempts=2)
    result = await provider.complete(prompt="test", schema=_SCHEMA)
    assert result["confidence"] == pytest.approx(0.7)


async def test_exhausted_retries_raises(httpx_mock: HTTPXMock) -> None:
    for _ in range(2):
        httpx_mock.add_response(url=_API_URL, status_code=503, text="unavailable")
    provider = AnthropicProvider(_KEY, timeout_seconds=5.0, max_attempts=2)
    with pytest.raises(LLMCallError):
        await provider.complete(prompt="test", schema=_SCHEMA)


async def test_implements_provider_protocol() -> None:
    from shared.llm.provider import LLMProvider

    provider = AnthropicProvider(_KEY)
    assert isinstance(provider, LLMProvider)
