# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
import respx
from httpx import ASGITransport, AsyncClient
from httpx import Request as HttpxRequest
from httpx import Response as HttpxResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.ingestion.app.main import create_app as create_ingestion
from services.patterns.app.main import create_app as create_patterns
from services.preprocessing.app.main import create_app as create_preprocess
from services.scoring.app.main import create_app as create_scoring
from shared.config import Settings
from shared.db.models import ScoreHistory as ScoreHistoryRow
from shared.db.models import SuspicionProfile as SuspicionProfileRow
from shared.db.session import tenant_session

pytestmark = pytest.mark.integration


async def _seed(engine: AsyncEngine, tenant_id: UUID) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                "VALUES (:tid, 'acme', 'free', '{}', 30, '{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"tid": str(tenant_id)},
        )


def _asgi_forwarder(app: Any) -> Any:
    async def _forward(request: HttpxRequest) -> HttpxResponse:
        origin = f"{request.url.scheme}://{request.url.host}"
        async with AsyncClient(transport=ASGITransport(app=app), base_url=origin) as inner:
            r = await inner.request(
                request.method,
                request.url.path,
                content=request.content,
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            )
        return HttpxResponse(r.status_code, content=r.content, headers=r.headers)

    return _forward


async def test_one_event_through_full_pipeline_updates_profile_and_history(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    await _seed(admin_engine, tenant_id)

    settings = Settings(
        env="test",
        preprocess_base_url="http://preprocess",
        patterns_base_url="http://patterns",
        scoring_base_url="http://score",
    )
    apps = {
        "preprocess": create_preprocess(settings),
        "patterns": create_patterns(settings),
        "score": create_scoring(settings),
    }
    ingestion = create_ingestion(settings)

    with respx.mock(assert_all_called=False) as router:
        for host, app in apps.items():
            router.route(host=host).mock(side_effect=_asgi_forwarder(app))
        router.route(host="127.0.0.1", port=6333).pass_through()
        body = {
            "idempotency_key": "e2e-1",
            "tenant_id": str(tenant_id),
            "conversation_id": str(uuid4()),
            "actor_external_id_hash": "a" * 64,
            "target_actor_external_id_hashes": ["b" * 64],
            "event_type": "message",
            "timestamp": datetime.now(UTC).isoformat(),
            "content": "don't tell your parents and lets move to signal",
            "metadata": {"recipient_age_bands": ["under_13"], "recipient_timezone": "UTC"},
        }
        async with AsyncClient(
            transport=ASGITransport(app=ingestion), base_url="http://test"
        ) as client:
            resp = await client.post("/v1/events", json=body)

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["current_score"] >= 40  # secrecy(+20) + migration(+18) + baseline(5) = 43
    assert payload["tier"] in {"active_monitor", "throttle"}

    async with tenant_session(tenant_id) as session:
        profile_row = (
            await session.execute(
                select(SuspicionProfileRow).where(SuspicionProfileRow.tenant_id == tenant_id)
            )
        ).scalar_one()
        history_rows = (
            (
                await session.execute(
                    select(ScoreHistoryRow).where(ScoreHistoryRow.tenant_id == tenant_id)
                )
            )
            .scalars()
            .all()
        )
    assert profile_row.current_score == payload["current_score"]
    assert len(history_rows) >= 2  # one per signal
