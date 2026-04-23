from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from uuid import UUID

from sentinel import EventType, SentinelClient


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode()).hexdigest()


def main() -> None:
    api_key = os.environ["SENTINEL_API_KEY"]
    base_url = os.environ.get("SENTINEL_BASE_URL", "https://api.sentinel.example.com")
    with SentinelClient(api_key=api_key, base_url=base_url) as client:
        result = client.events.message(
            tenant_id=UUID(os.environ["SENTINEL_TENANT_ID"]),
            conversation_id=UUID("11111111-1111-1111-1111-111111111111"),
            actor_external_id_hash=hash_user_id("platform-user-42"),
            content="Hello from the SENTINEL Python SDK!",
            timestamp=datetime.now(UTC),
            event_type=EventType.MESSAGE,
            metadata={"platform": "example-app", "channel": "dm"},
        )
        print(f"tier={result.tier.name.lower()} score={result.current_score} delta={result.delta}")


if __name__ == "__main__":
    main()
