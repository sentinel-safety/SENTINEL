# Integration Guide

This guide covers the cross-cutting concerns shared by both SDKs.

## Table of contents

- [Platforms and modes](#platforms-and-modes)
- [Event payload shape](#event-payload-shape)
- [Hashing actor identifiers](#hashing-actor-identifiers)
- [Idempotency](#idempotency)
- [Retries and Retry-After](#retries-and-retry-after)
- [Fail-open semantics](#fail-open-semantics)
- [Webhook signature verification](#webhook-signature-verification)
- [Webhook delivery guarantees](#webhook-delivery-guarantees)
- [Testing your integration](#testing-your-integration)

## Platforms and modes

SENTINEL runs in one of three modes per tenant:

| Mode | Description |
|---|---|
| Advisory | SENTINEL returns scores only; your platform decides what to do. Safe default. |
| Auto-enforce | SENTINEL calls back with recommended actions; your platform executes them. |
| Hybrid | Auto-enforce up to tier N, advisory above. |

Your SDK code is identical in all three modes — only the tenant configuration changes.

## Event payload shape

Every `events.message(...)` call produces this JSON body:

```json
{
  "idempotency_key": "uuid-v4",
  "tenant_id": "uuid",
  "conversation_id": "uuid",
  "actor_external_id_hash": "<64-char lowercase hex SHA-256>",
  "target_actor_external_id_hashes": ["<64-char lowercase hex SHA-256>", "..."],
  "event_type": "message",
  "timestamp": "2026-04-20T12:34:56.000+00:00",
  "content": "...",
  "metadata": { "arbitrary": "json" }
}
```

The server responds with:

```json
{
  "event_id": "uuid",
  "current_score": 42,
  "previous_score": 30,
  "delta": 12,
  "tier": "watch",
  "signals": []
}
```

## Hashing actor identifiers

**The SDK never hashes for you.** You control:

- Which underlying identifier to use (platform user ID, email, device ID, …).
- Whether to salt the hash (recommended for privacy).
- How to keep the salt stable over time (required; changing the salt breaks all historical actor tracking).

A minimal hashing helper:

**Python**

```python
import hashlib

def hash_actor(user_id: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{user_id}".encode()).hexdigest()
```

**Node**

```typescript
import { createHash } from "node:crypto";

export function hashActor(userId: string, salt: string): string {
  return createHash("sha256").update(`${salt}:${userId}`).digest("hex");
}
```

Both SDKs reject `actor_external_id_hash` values that do not match `^[a-f0-9]{64}$` before making an HTTP call.

## Idempotency

Every event carries an `idempotency_key`. If you call `events.message(...)` twice with the same key, SENTINEL returns the same score response both times — it does NOT re-process the event.

- **If you omit `idempotencyKey` / `idempotency_key`**, the SDK generates a fresh uuid4 per call. Good for most scenarios.
- **If you retry from application code after a failure**, you MUST reuse the same key.

## Retries and Retry-After

Both SDKs retry up to 3 times (configurable) on:

- 5xx responses.
- Connection errors and timeouts.
- 429 with `Retry-After` honored up to `retryCapSeconds` / `retry_cap_seconds` (default 30 s).

They do NOT retry on:

- 2xx (obviously).
- 4xx other than 429 — these indicate caller bugs (malformed payload, bad credentials).
- `AuthError` (401 / 403).

Backoff doubles from `retry_base_seconds` (default 0.5 s) up to `retry_cap_seconds`.

## Fail-open semantics

After the final retry fails, the SDKs return a fallback `ScoreResult`:

```json
{
  "currentScore": 0,
  "previousScore": 0,
  "delta": 0,
  "tier": "trusted",
  "reasoning": null
}
```

and emit a warning log line like:

```
sentinel fail-open: returning trusted fallback after 3 attempts (...)
```

**Why:** if SENTINEL is down, your platform must still serve users. The fallback lets normal traffic flow through. Set up alerting on the warning so you know when SENTINEL is unreachable.

**Detection recipe:** check `reasoning is None` AND a flag from your own logging pipeline. A missing `reasoning` alone is not proof of fail-open — it also means "no tier change occurred."

## Webhook signature verification

SENTINEL posts signed deliveries to endpoints you register. Each request carries:

| Header | Meaning |
|---|---|
| `X-Sentinel-Signature` | `t=<unix>,v1=<hex>` |
| `X-Sentinel-Event` | event kind (`tier.changed`, `pattern.matched`, …) |
| `X-Sentinel-Delivery` | unique delivery UUID (use for dedup) |

The signature covers `"<unix>."` + the raw body bytes, HMAC-SHA256 with your tenant webhook secret.

**Verification recipe (Python):**

```python
import os
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, Request

from sentinel import verify_webhook_signature, WebhookSignatureError

app = FastAPI()

@app.post("/sentinel/webhook")
async def sentinel_webhook(request: Request) -> dict:
    body = await request.body()
    try:
        verify_webhook_signature(
            header=request.headers.get("X-Sentinel-Signature", ""),
            secret=os.environ["SENTINEL_WEBHOOK_SECRET"],
            body=body,
            now=datetime.now(UTC),
            skew_seconds=300,
        )
    except WebhookSignatureError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    return {"status": "ok"}
```

**Verification recipe (Node):**

```typescript
import { verifyWebhookSignature, WebhookSignatureError } from "@sentinel/client";

function verify(req, rawBody) {
  try {
    verifyWebhookSignature({
      header: req.headers["x-sentinel-signature"],
      secret: process.env.SENTINEL_WEBHOOK_SECRET,
      body: rawBody,
      now: new Date(),
      skewSeconds: 300
    });
  } catch (err) {
    if (err instanceof WebhookSignatureError) {
      return 401;
    }
    throw err;
  }
  return 200;
}
```

**Critical rule:** use the raw request body (not a re-serialized JSON object). The server signs exact bytes with sorted keys. If you parse and re-serialize you will almost always get a different byte sequence and the signature will fail.

## Webhook delivery guarantees

- **At-least-once.** Same delivery may arrive multiple times. Deduplicate on `X-Sentinel-Delivery`.
- **Unordered.** Do not depend on arrival order.
- **Retries** with exponential backoff over ~30 minutes. After exhaustion the delivery goes to the tenant dead-letter queue and surfaces on the dashboard.
- **Timeout.** You have 5 seconds to respond with a 2xx.

## Testing your integration

- Use a dedicated non-production tenant for development.
- For unit tests, inject a mock HTTP client (Python: `httpx.MockTransport` or `respx`; Node: pass a custom `fetchImpl`).
- For webhook verification tests, sign bodies with the same HMAC-SHA256 scheme your handler expects — see `sdk/python/tests/test_webhooks.py` and `sdk/node/tests/webhooks.test.ts` for reference implementations.
- Exercise the fail-open path deliberately in staging by pointing the SDK at an unroutable base URL and observing that your platform continues to function.
