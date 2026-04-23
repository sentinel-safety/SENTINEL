# Python SDK Quickstart

Target: first event submitted and scored within 30 minutes.

## 1. Install

Build the wheel locally:

```bash
cd sdk/python && uv build
```

Install it into your project:

```bash
pip install /path/to/sentinel/sdk/python/dist/sentinel_python-0.1.0-py3-none-any.whl
```

## 2. Get credentials

You need:

- A tenant API key (`sk_...`) from the SENTINEL dashboard.
- Your tenant UUID.
- The API base URL (for example `https://api.sentinel.example.com`).

Set them in your environment:

```bash
export SENTINEL_API_KEY=sk_live_...
export SENTINEL_BASE_URL=https://api.sentinel.example.com
export SENTINEL_TENANT_ID=00000000-0000-0000-0000-000000000001
```

## 3. Send your first event

Create `send_event.py`:

```python
from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from uuid import UUID

from sentinel import EventType, SentinelClient


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode()).hexdigest()


def main() -> None:
    with SentinelClient(
        api_key=os.environ["SENTINEL_API_KEY"],
        base_url=os.environ["SENTINEL_BASE_URL"],
    ) as client:
        result = client.events.message(
            tenant_id=UUID(os.environ["SENTINEL_TENANT_ID"]),
            conversation_id=UUID("11111111-1111-1111-1111-111111111111"),
            actor_external_id_hash=hash_user_id("my-first-user"),
            content="hello from my first SENTINEL integration",
            timestamp=datetime.now(UTC),
            event_type=EventType.MESSAGE,
            metadata={"platform": "my-app", "channel": "dm"},
        )
        print(f"tier={result.tier.name.lower()} score={result.current_score} delta={result.delta}")


if __name__ == "__main__":
    main()
```

Run it:

```bash
python send_event.py
```

You should see output like:

```
tier=trusted score=0 delta=0
```

## 4. React to the result

The common pattern is to act on the tier:

```python
from sentinel import ResponseTier

if result.tier >= ResponseTier.THROTTLE:
    throttle_actor(user_id)
elif result.tier >= ResponseTier.WATCH:
    flag_for_review(user_id)
```

## 5. Next steps

- Read the [Python API reference](./api-reference-python.md).
- Add [webhook signature verification](./integration-guide.md#webhook-signature-verification) so SENTINEL can push tier-change events to your platform.
- Learn about [idempotency and fail-open semantics](./integration-guide.md).
