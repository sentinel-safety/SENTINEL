# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
import respx
from httpx import ASGITransport, AsyncClient
from httpx import Request as HttpxRequest
from httpx import Response as HttpxResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.ingestion.app.main import create_app
from shared.audit.chain import verify_chain
from shared.config import Settings
from shared.db.session import tenant_session

pytestmark = pytest.mark.integration


async def _seed(engine: AsyncEngine, tenant_id: Any) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                "VALUES (:tid, 'acme', 'free', '{}', 30, '{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"tid": str(tenant_id)},
        )


async def test_ingestion_pipeline_end_to_end_against_in_process_services(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    from services.patterns.app.main import create_app as create_patterns
    from services.preprocessing.app.main import create_app as create_preprocess
    from services.scoring.app.main import create_app as create_scoring

    tenant_id = uuid4()
    await _seed(admin_engine, tenant_id)

    preprocess_app = create_preprocess(Settings(env="test"))
    patterns_app = create_patterns(Settings(env="test"))
    scoring_app = create_scoring(Settings(env="test"))

    settings = Settings(
        env="test",
        preprocess_base_url="http://preprocess",
        patterns_base_url="http://patterns",
        scoring_base_url="http://score",
    )
    ingestion_app = create_app(settings)

    with respx.mock(assert_all_called=False) as router:
        router.route(host="preprocess").mock(side_effect=_asgi_forwarder(preprocess_app))
        router.route(host="patterns").mock(side_effect=_asgi_forwarder(patterns_app))
        router.route(host="score").mock(side_effect=_asgi_forwarder(scoring_app))
        router.route(host="127.0.0.1", port=6333).pass_through()

        body = {
            "idempotency_key": "k-1",
            "tenant_id": str(tenant_id),
            "conversation_id": str(uuid4()),
            "actor_external_id_hash": "a" * 64,
            "target_actor_external_id_hashes": ["b" * 64],
            "event_type": "message",
            "timestamp": datetime.now(UTC).isoformat(),
            "content": "don't tell your parents",
            "metadata": {"recipient_age_bands": ["under_13"], "recipient_timezone": "UTC"},
        }

        async with AsyncClient(
            transport=ASGITransport(app=ingestion_app), base_url="http://test"
        ) as client:
            resp = await client.post("/v1/events", json=body)
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["tier"] in {"trusted", "watch", "active_monitor"}
    assert payload["current_score"] > 5

    async with tenant_session(tenant_id) as session:
        assert await verify_chain(session, tenant_id) >= 1


def _asgi_forwarder(app: Any) -> Callable[[HttpxRequest], Coroutine[Any, Any, HttpxResponse]]:
    async def _forward(request: HttpxRequest) -> HttpxResponse:
        base = f"{request.url.scheme}://{request.url.host}"
        async with AsyncClient(transport=ASGITransport(app=app), base_url=base) as inner:
            inner_response = await inner.request(
                request.method,
                request.url.path,
                content=request.content,
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            )
        return HttpxResponse(
            inner_response.status_code,
            content=inner_response.content,
            headers=inner_response.headers,
        )

    return _forward
