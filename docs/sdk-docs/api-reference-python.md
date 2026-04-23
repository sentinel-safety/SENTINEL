# Python SDK API Reference

Module: `sentinel` (package `sentinel-python`, version 0.1.0).

## `SentinelClient`

```python
SentinelClient(
    *,
    api_key: str,
    base_url: str,
    timeout: float = 10.0,
    retry_attempts: int = 3,
    retry_base_seconds: float = 0.5,
    retry_cap_seconds: float = 30.0,
    http_client: httpx.Client | None = None,
)
```

Thread-safe synchronous client. Use as a context manager or call `.close()` to release the underlying HTTP connection pool.

### Attributes

- `events: EventsAPI` — see below.

### Methods

- `close() -> None` — close the internal `httpx.Client`.

## `client.events.message(...)`

```python
client.events.message(
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
) -> ScoreResult
```

Submit a scoring event. Returns a `ScoreResult`.

### Required arguments

- `tenant_id` — your tenant UUID.
- `conversation_id` — stable UUID identifying the conversation.
- `actor_external_id_hash` — **lowercase hex SHA-256 of the actor's platform ID**. The SDK validates against `^[a-f0-9]{64}$`. The SDK does NOT hash for you — you own the salting strategy.
- `content` — message body (UTF-8, up to 20 000 characters).
- `timestamp` — timezone-aware `datetime`; naive datetimes raise `ValueError`.

### Optional arguments

- `event_type` — one of `EventType.{MESSAGE,IMAGE,FRIEND_REQUEST,GIFT,PROFILE_CHANGE,VOICE_CLIP}`. Defaults to `MESSAGE`.
- `target_actor_external_id_hashes` — tuple of target actor hashes. Each must match `^[a-f0-9]{64}$`.
- `metadata` — free-form JSON-serializable dictionary.
- `idempotency_key` — string up to 200 characters. If omitted the SDK generates a fresh `uuid4` per call.

### Raised exceptions

| Exception | When |
|---|---|
| `ValueError` | Malformed hash, naive timestamp, empty `api_key` / `base_url`. |
| `AuthError` | HTTP 401 / 403. **Not retried.** |
| All other transport / 5xx errors | Fail-open: returns a trusted fallback `ScoreResult` after `retry_attempts` attempts. |

## Models

### `ScoreResult`

```python
class ScoreResult:
    current_score: int            # 0-100
    previous_score: int           # 0-100
    delta: int
    tier: ResponseTier
    reasoning: Reasoning | None   # None on fail-open and when no tier change
```

### `ResponseTier`

`IntEnum` with members `TRUSTED=0`, `WATCH=1`, `ACTIVE_MONITOR=2`, `THROTTLE=3`, `RESTRICT=4`, `CRITICAL=5`. Serializes to its lowercase name (`"trusted"`, `"watch"`, …).

### `EventType`

`StrEnum`: `MESSAGE`, `IMAGE`, `FRIEND_REQUEST`, `GIFT`, `PROFILE_CHANGE`, `VOICE_CLIP`.

### `ActionKind`

`StrEnum`: `NONE`, `SILENT_LOG`, `REVIEW_QUEUE`, `THROTTLE_DM_TO_MINORS`, `DISABLE_MEDIA_TO_MINORS`, `REQUIRE_APPROVAL_TO_FRIEND_MINOR`, `RESTRICT_TO_PUBLIC_POSTS`, `BLOCK_DM_TO_MINORS`, `ACCOUNT_WARNING`, `SUSPEND`, `MANDATORY_REPORT`.

### `Reasoning`

```python
class Reasoning:
    actor_id: UUID
    tenant_id: UUID
    score_change: int
    new_score: int                    # 0-100
    new_tier: ResponseTier
    primary_drivers: tuple[PrimaryDriver, ...]
    context: str
    recommended_action_summary: str
    generated_at: datetime
    next_review_at: datetime | None
```

### `PrimaryDriver`

```python
class PrimaryDriver:
    pattern: str              # human-readable name, e.g. "Late-night contact"
    pattern_id: str           # slug, e.g. "late_night"
    confidence: float         # 0.0 - 1.0
    evidence: str             # rendered human-readable evidence string
```

### `RecommendedAction`

```python
class RecommendedAction:
    kind: ActionKind
    description: str
    parameters: dict[str, Any]
```

## Errors

```
SentinelError
├── AuthError
├── RateLimitError(retry_after_seconds: float | None)
├── TimeoutError
└── ServerError(status_code: int)
```

## Webhook verification

```python
verify_webhook_signature(
    *,
    header: str,       # raw X-Sentinel-Signature header value
    secret: str,       # tenant webhook secret
    body: bytes,       # raw request body bytes
    now: datetime,     # typically datetime.now(UTC)
    skew_seconds: int = 300,
) -> None
```

Raises `WebhookSignatureError` on any mismatch (malformed header, tampered body, wrong secret, timestamp outside skew window). Returns `None` on success.

**You must pass the raw body bytes.** Parsing and re-serializing the JSON will change the byte sequence and break the signature.
