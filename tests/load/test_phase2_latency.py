# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import time
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
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

pytestmark = pytest.mark.load

_TARGET_P99_MS = 300.0
_EVENTS = 1000


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


def _asgi_forwarder(
    app: Any,
) -> Callable[[HttpxRequest], Coroutine[Any, Any, HttpxResponse]]:
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


async def test_phase2_p99_latency_stays_under_budget(
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

    durations_ms: list[float] = []
    with respx.mock(assert_all_called=False) as router:
        for host, app in apps.items():
            router.route(host=host).mock(side_effect=_asgi_forwarder(app))
        router.route(host="127.0.0.1", port=6333).pass_through()

        async with AsyncClient(
            transport=ASGITransport(app=ingestion), base_url="http://test"
        ) as client:
            for i in range(_EVENTS):
                body = {
                    "idempotency_key": f"phase2-load-{i}",
                    "tenant_id": str(tenant_id),
                    "conversation_id": str(uuid4()),
                    "actor_external_id_hash": "a" * 64,
                    "target_actor_external_id_hashes": ["b" * 64],
                    "event_type": "message",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "content": "hello there friend",
                    "metadata": {
                        "recipient_age_bands": ["under_13"],
                        "recipient_timezone": "UTC",
                    },
                }
                start = time.perf_counter()
                resp = await client.post("/v1/events", json=body)
                durations_ms.append((time.perf_counter() - start) * 1000)
                assert resp.status_code == 200

    durations_ms.sort()
    p99 = durations_ms[int(len(durations_ms) * 0.99) - 1]
    assert p99 < _TARGET_P99_MS, (
        f"p99={p99:.2f}ms exceeds budget of {_TARGET_P99_MS}ms (samples={len(durations_ms)})"
    )
