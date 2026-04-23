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


async def test_503_returns_retryable() -> None:
    url = "https://tenant.example/hook"
    with respx.mock() as mock:
        mock.post(url).mock(return_value=Response(503))
        async with AsyncClient() as http:
            outcome = await deliver_webhook(
                http=http,
                url=url,
                envelope=_envelope(),
                secret="a" * 64,
                now=datetime.now(UTC),
                timeout_seconds=2.0,
            )
    assert outcome == DeliveryOutcome.RETRYABLE


async def test_400_returns_non_retryable() -> None:
    url = "https://tenant.example/hook"
    with respx.mock() as mock:
        mock.post(url).mock(return_value=Response(400))
        async with AsyncClient() as http:
            outcome = await deliver_webhook(
                http=http,
                url=url,
                envelope=_envelope(),
                secret="a" * 64,
                now=datetime.now(UTC),
                timeout_seconds=2.0,
            )
    assert outcome == DeliveryOutcome.NON_RETRYABLE
