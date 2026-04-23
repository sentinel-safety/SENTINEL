# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from sqlalchemy import literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models import WebhookEndpoint as WebhookEndpointRow
from shared.response.envelope import WebhookEventKind
from shared.schemas.tenant import WebhookEndpoint


async def list_endpoints_for_event(
    session: AsyncSession, *, tenant_id: UUID, event_kind: WebhookEventKind
) -> tuple[WebhookEndpoint, ...]:
    stmt = (
        select(WebhookEndpointRow)
        .where(
            WebhookEndpointRow.tenant_id == tenant_id,
            WebhookEndpointRow.active.is_(True),
            literal(event_kind.value) == WebhookEndpointRow.subscribed_topics.any_(),
        )
        .order_by(WebhookEndpointRow.created_at)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return tuple(
        WebhookEndpoint(
            id=row.id,
            tenant_id=row.tenant_id,
            url=row.url,
            events=tuple(row.subscribed_topics),
            secret_hash=row.secret_hash,
            active=row.active,
            created_at=row.created_at,
        )
        for row in rows
    )
