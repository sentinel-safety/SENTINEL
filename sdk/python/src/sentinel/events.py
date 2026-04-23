from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from re import fullmatch
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sentinel._retry import compute_backoff, parse_retry_after
from sentinel.errors import (
    AuthError,
    RateLimitError,
    SentinelError,
    ServerError,
)
from sentinel.errors import TimeoutError as SentinelTimeoutError
from sentinel.models import EventType, ResponseTier, ScoreResult

if TYPE_CHECKING:
    from sentinel.client import SentinelClient

logger = logging.getLogger("sentinel")

_HASH_PATTERN = r"^[a-f0-9]{64}$"


def _serialize_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.isoformat()


def _validate_hash(label: str, value: str) -> None:
    if fullmatch(_HASH_PATTERN, value) is None:
        raise ValueError(f"{label} must be a lowercase hex SHA256 string (64 chars, [a-f0-9])")


def _fallback_result() -> ScoreResult:
    return ScoreResult(
        current_score=0,
        previous_score=0,
        delta=0,
        tier=ResponseTier.TRUSTED,
        reasoning=None,
    )


class EventsAPI:
    def __init__(self, *, client: SentinelClient) -> None:
        self._client = client

    def message(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        actor_external_id_hash: str,
        content: str,
        timestamp: datetime,
        event_type: EventType = EventType.MESSAGE,
        target_actor_external_id_hashes: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> ScoreResult:
        _validate_hash("actor_external_id_hash", actor_external_id_hash)
        for target in target_actor_external_id_hashes:
            _validate_hash("target_actor_external_id_hashes[*]", target)
        key = idempotency_key or str(uuid4())
        body: dict[str, Any] = {
            "idempotency_key": key,
            "tenant_id": str(tenant_id),
            "conversation_id": str(conversation_id),
            "actor_external_id_hash": actor_external_id_hash,
            "target_actor_external_id_hashes": list(target_actor_external_id_hashes),
            "event_type": event_type.value,
            "timestamp": _serialize_timestamp(timestamp),
            "content": content,
            "metadata": metadata or {},
        }
        return self._send_with_retries(body)

    def _send_with_retries(self, body: dict[str, Any]) -> ScoreResult:
        attempts = self._client.retry_attempts
        base = self._client.retry_base_seconds
        cap = self._client.retry_cap_seconds
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                response = self._client.request_json(
                    method="POST", path="/v1/events", json_body=body
                )
                return self._parse_response(response.json())
            except AuthError:
                raise
            except RateLimitError as exc:
                last_error = exc
                if attempt >= attempts:
                    break
                raw = str(exc.retry_after_seconds) if exc.retry_after_seconds is not None else None
                hint = parse_retry_after(raw, now=datetime.now(UTC))
                delay = (
                    min(cap, hint)
                    if hint is not None
                    else compute_backoff(attempt=attempt, base=base, cap=cap)
                )
                time.sleep(delay)
                continue
            except (ServerError, SentinelTimeoutError, SentinelError) as exc:
                last_error = exc
                if attempt >= attempts:
                    break
                time.sleep(compute_backoff(attempt=attempt, base=base, cap=cap))
                continue
        logger.warning(
            "sentinel fail-open: returning trusted fallback after %s attempts (%s)",
            attempts,
            last_error,
        )
        return _fallback_result()

    @staticmethod
    def _parse_response(payload: dict[str, Any]) -> ScoreResult:
        if "previous_score" not in payload:
            payload = {
                **payload,
                "previous_score": max(
                    0, int(payload.get("current_score", 0)) - int(payload.get("delta", 0))
                ),
            }
        return ScoreResult.model_validate(payload)
