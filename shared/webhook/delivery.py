# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime
from enum import StrEnum

import httpx

from shared.response.envelope import WebhookEnvelope
from shared.webhook.signing import build_signature_header


class DeliveryOutcome(StrEnum):
    SUCCESS = "success"
    RETRYABLE = "retryable"
    NON_RETRYABLE = "non_retryable"


_SIGNATURE_HEADER = "X-Sentinel-Signature"
_EVENT_HEADER = "X-Sentinel-Event"
_DELIVERY_HEADER = "X-Sentinel-Delivery"


async def deliver_webhook(
    *,
    http: httpx.AsyncClient,
    url: str,
    envelope: WebhookEnvelope,
    secret: str,
    now: datetime,
    timeout_seconds: float,
) -> DeliveryOutcome:
    body = envelope.body_bytes()
    headers = {
        _SIGNATURE_HEADER: build_signature_header(secret=secret, timestamp=now, body=body),
        _EVENT_HEADER: envelope.event_kind.value,
        _DELIVERY_HEADER: str(envelope.delivery_id),
        "Content-Type": "application/json",
    }
    try:
        response = await http.post(url, content=body, headers=headers, timeout=timeout_seconds)
    except (httpx.TimeoutException, httpx.TransportError):
        return DeliveryOutcome.RETRYABLE
    if 200 <= response.status_code < 300:
        return DeliveryOutcome.SUCCESS
    if 500 <= response.status_code < 600 or response.status_code == 429:
        return DeliveryOutcome.RETRYABLE
    return DeliveryOutcome.NON_RETRYABLE
