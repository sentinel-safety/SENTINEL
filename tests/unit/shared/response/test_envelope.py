# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import orjson
import pytest

from shared.response.envelope import WebhookEnvelope, WebhookEventKind

pytestmark = pytest.mark.unit


def test_envelope_produces_stable_body() -> None:
    env = WebhookEnvelope(
        delivery_id=uuid4(),
        tenant_id=uuid4(),
        actor_id=uuid4(),
        event_kind=WebhookEventKind.TIER_CHANGED,
        body={"previous_tier": 2, "new_tier": 4, "new_score": 80},
        produced_at=datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC),
    )
    raw = env.body_bytes()
    parsed = orjson.loads(raw)
    assert parsed["event_kind"] == "tier.changed"
    assert parsed["payload"]["previous_tier"] == 2


def test_event_kind_validated() -> None:
    with pytest.raises(ValueError):
        WebhookEnvelope(
            delivery_id=uuid4(),
            tenant_id=uuid4(),
            actor_id=uuid4(),
            event_kind="not-a-known-kind",
            body={},
            produced_at=datetime.now(UTC),
        )
