# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.response.app.endpoint_repository import list_endpoints_for_event
from shared.db.session import tenant_session
from shared.response.envelope import WebhookEventKind

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed(admin_engine: AsyncEngine) -> UUID:
    tid = uuid4()
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) VALUES (:t, 'acme', 'free', '{}', 30, '{}'::jsonb)"
            ),
            {"t": str(tid)},
        )
        await conn.execute(
            text(
                "INSERT INTO webhook_endpoint (id, tenant_id, url, secret_hash, "
                "subscribed_topics, active) VALUES "
                "(:id, :t, 'https://a.example/hook', :sh, ARRAY['tier.changed'], true)"
            ),
            {"id": str(uuid4()), "t": str(tid), "sh": "a" * 64},
        )
        await conn.execute(
            text(
                "INSERT INTO webhook_endpoint (id, tenant_id, url, secret_hash, "
                "subscribed_topics, active) VALUES "
                "(:id, :t, 'https://b.example/hook', :sh, ARRAY['mandatory_report.required'], true)"
            ),
            {"id": str(uuid4()), "t": str(tid), "sh": "b" * 64},
        )
        await conn.execute(
            text(
                "INSERT INTO webhook_endpoint (id, tenant_id, url, secret_hash, "
                "subscribed_topics, active) VALUES "
                "(:id, :t, 'https://inactive.example/hook', :sh, "
                "ARRAY['tier.changed'], false)"
            ),
            {"id": str(uuid4()), "t": str(tid), "sh": "c" * 64},
        )
    return tid


async def test_returns_only_active_endpoints_subscribed_to_kind(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = await _seed(admin_engine)
    async with tenant_session(tid) as session:
        endpoints = await list_endpoints_for_event(
            session, tenant_id=tid, event_kind=WebhookEventKind.TIER_CHANGED
        )
    urls = [str(e.url) for e in endpoints]
    assert urls == ["https://a.example/hook"]


async def test_filters_to_subscribed_kind_only(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = await _seed(admin_engine)
    async with tenant_session(tid) as session:
        endpoints = await list_endpoints_for_event(
            session, tenant_id=tid, event_kind=WebhookEventKind.MANDATORY_REPORT_REQUIRED
        )
    urls = [str(e.url) for e in endpoints]
    assert urls == ["https://b.example/hook"]
