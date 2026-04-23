# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
import respx

from shared.response.envelope import WebhookEnvelope, WebhookEventKind
from shared.webhook.delivery import DeliveryOutcome, deliver_webhook

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _envelope() -> WebhookEnvelope:
    return WebhookEnvelope(
        delivery_id=uuid4(),
        tenant_id=uuid4(),
        actor_id=uuid4(),
        event_kind=WebhookEventKind.TIER_CHANGED,
        body={"new_tier": 4},
        produced_at=datetime.now(UTC),
    )


async def test_timeout_returns_retryable() -> None:
    url = "https://tenant.example/hook"
    with respx.mock() as mock:
        mock.post(url).mock(side_effect=httpx.TimeoutException("t"))
        async with httpx.AsyncClient() as http:
            outcome = await deliver_webhook(
                http=http,
                url=url,
                envelope=_envelope(),
                secret="a" * 64,
                now=datetime.now(UTC),
                timeout_seconds=0.1,
            )
    assert outcome == DeliveryOutcome.RETRYABLE
