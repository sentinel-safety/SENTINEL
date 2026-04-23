# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
import respx
from httpx import ASGITransport, AsyncClient
from httpx import Request as HttpxRequest
from httpx import Response as HttpxResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.ingestion.app.main import create_app as create_ingestion
from services.patterns.app.main import create_app as create_patterns
from services.preprocessing.app.main import create_app as create_preprocess
from services.scoring.app.main import create_app as create_scoring
from shared.config import Settings

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def _forwarder(app: Any) -> Any:
    async def _f(request: HttpxRequest) -> HttpxResponse:
        origin = f"{request.url.scheme}://{request.url.host}"
        async with AsyncClient(transport=ASGITransport(app=app), base_url=origin) as inner:
            r = await inner.request(
                request.method,
                request.url.path,
                content=request.content,
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            )
        return HttpxResponse(r.status_code, content=r.content, headers=r.headers)

    return _f


async def _seed(engine: AsyncEngine, tenant_id: UUID) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) VALUES (:t, 'acme', 'free', '{}', 30, "
                "'{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"t": str(tenant_id)},
        )


async def test_score_accumulates_across_five_conversations(
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

    actor_hash = "a" * 64
    last_score = 0
    with respx.mock(assert_all_called=False) as router:
        for host, app in apps.items():
            router.route(host=host).mock(side_effect=_forwarder(app))
        router.route(host="127.0.0.1", port=6333).pass_through()
        async with AsyncClient(
            transport=ASGITransport(app=ingestion), base_url="http://test"
        ) as client:
            base_time = datetime.now(UTC) - timedelta(days=15)
            for conv_idx in range(5):
                conv_id = str(uuid4())
                for msg_idx in range(2):
                    idem = f"span-{conv_idx}-{msg_idx}"
                    ts = base_time + timedelta(days=conv_idx * 2, hours=msg_idx)
                    resp = await client.post(
                        "/v1/events",
                        json={
                            "idempotency_key": idem,
                            "tenant_id": str(tenant_id),
                            "conversation_id": conv_id,
                            "actor_external_id_hash": actor_hash,
                            "target_actor_external_id_hashes": [f"{conv_idx:064x}"],
                            "event_type": "message",
                            "timestamp": ts.isoformat(),
                            "content": "don't tell your parents about me"
                            if msg_idx == 0
                            else "hi friend",
                            "metadata": {
                                "recipient_age_bands": ["under_13"],
                                "recipient_timezone": "UTC",
                            },
                        },
                    )
                    assert resp.status_code == 200
                    current = resp.json()["current_score"]
                    assert current >= last_score - 1
                    last_score = current
    assert last_score > 20
