# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import json
from typing import Any

import httpx
from jsonschema import ValidationError, validate
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from shared.llm.provider import LLMCallError, LLMValidationError

_API_URL = "https://api.anthropic.com/v1/messages"
_MODEL = "claude-3-5-haiku-20241022"
_MAX_TOKENS = 1024


class AnthropicProvider:
    def __init__(
        self,
        api_key: str,
        *,
        timeout_seconds: float = 30.0,
        max_attempts: int = 3,
    ) -> None:
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._max_attempts = max_attempts

    async def complete(self, *, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        return await self._call_with_retry(prompt=prompt, schema=schema)

    async def _call_with_retry(self, *, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        attempt_fn = retry(
            retry=retry_if_exception_type(LLMCallError),
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
            reraise=True,
        )(self._attempt)
        return await attempt_fn(prompt=prompt, schema=schema)

    async def _attempt(self, *, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        system = (
            "You are a JSON-only responder. "
            f"Respond with a single JSON object matching this schema: {json.dumps(schema)}. "
            "No explanation, no markdown, just the JSON object."
        )
        body = {
            "model": _MODEL,
            "max_tokens": _MAX_TOKENS,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(_API_URL, json=body, headers=headers)
        except httpx.TimeoutException as exc:
            raise LLMCallError("anthropic request timed out") from exc
        except httpx.HTTPError as exc:
            raise LLMCallError(f"anthropic http error: {exc}") from exc

        if response.status_code != 200:
            raise LLMCallError(f"anthropic error {response.status_code}: {response.text}")

        raw = response.json()
        text = raw["content"][0]["text"]
        try:
            payload: dict[str, Any] = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMCallError(f"anthropic returned non-json: {text!r}") from exc

        try:
            validate(payload, schema)
        except ValidationError as exc:
            raise LLMValidationError(str(exc)) from exc

        return payload
