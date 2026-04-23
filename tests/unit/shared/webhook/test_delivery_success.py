# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
import respx
from httpx import AsyncClient, Response

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


async def test_200_returns_success() -> None:
    env = _envelope()
    url = "https://tenant.example/hook"
    with respx.mock() as mock:
        route = mock.post(url).mock(return_value=Response(200))
        async with AsyncClient() as http:
            outcome = await deliver_webhook(
                http=http,
                url=url,
                envelope=env,
                secret="a" * 64,
                now=datetime.now(UTC),
                timeout_seconds=2.0,
            )
    assert outcome == DeliveryOutcome.SUCCESS
    assert route.called
