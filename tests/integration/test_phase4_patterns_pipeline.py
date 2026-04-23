# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.patterns.app.main import create_app as create_patterns
from shared.config import get_settings

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed(engine: AsyncEngine, tenant_id, actor_id) -> None:  # type: ignore[no-untyped-def]
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) VALUES (:t, 'acme', 'free', '{}', 30, "
                "'{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"t": str(tenant_id)},
        )
        await conn.execute(
            text(
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band, metadata) "
                "VALUES (:a, :t, :h, 'unknown', '{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"a": str(actor_id), "t": str(tenant_id), "h": "f" * 64},
        )


async def test_detect_writes_graph_edge_and_invokes_fingerprint(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant = uuid4()
    actor = uuid4()
    target = uuid4()
    await _seed(admin_engine, tenant, actor)
    await _seed(admin_engine, tenant, target)

    settings = get_settings()
    app = create_patterns(settings)
    event_id = uuid4()
    payload = {
        "event": {
            "id": str(event_id),
            "tenant_id": str(tenant),
            "conversation_id": str(uuid4()),
            "actor_id": str(actor),
            "target_actor_ids": [str(target)],
            "timestamp": datetime.now(UTC).isoformat(),
            "type": "message",
            "content_hash": "a" * 64,
            "content_features": {"minor_recipient": True, "normalized_content": "hi"},
        },
        "features": {
            "normalized_content": "hi",
            "language": "en",
            "token_count": 1,
            "contains_url": False,
            "contains_contact_request": False,
            "minor_recipient": True,
            "late_night_local": False,
        },
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/internal/detect", json=payload)
    assert resp.status_code == 200, resp.text

    async with admin_engine.begin() as conn:
        await conn.execute(text("SET search_path = ag_catalog, public"))
        row = await conn.execute(
            text(
                "SELECT * FROM ag_catalog.cypher('sentinel_graph', $$ "
                "MATCH (a:Actor {actor_id: '" + str(actor) + "'})-[r:INTERACTED_WITH]->"
                "(b:Actor {actor_id: '" + str(target) + "'}) "
                "RETURN count(r) $$) AS (n agtype)"
            )
        )
        scalar = str(row.scalar_one())
        assert scalar.strip('"') == "1", f"got scalar: {scalar!r}"
