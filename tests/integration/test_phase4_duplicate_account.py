# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
import respx
import yaml
from httpx import ASGITransport, AsyncClient
from httpx import Request as HttpxRequest
from httpx import Response as HttpxResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.ingestion.app.main import create_app as create_ingestion
from services.patterns.app.main import create_app as create_patterns
from services.patterns.app.repositories.feature_window import (
    aggregate_window_from_rows,
    fetch_window_rows,
)
from services.preprocessing.app.main import create_app as create_preprocess
from services.scoring.app.main import create_app as create_scoring
from shared.config import Settings, get_settings
from shared.db.session import tenant_session
from shared.fingerprint.features import compute_fingerprint
from shared.fingerprint.repository import upsert_fingerprint
from shared.vector.qdrant_client import QdrantAdapter, get_qdrant_client

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_SCENARIO = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "scenarios"
    / "duplicate_account_predator.yaml"
)


def _forwarder(app: Any) -> Any:
    async def _f(req: HttpxRequest) -> HttpxResponse:
        origin = f"{req.url.scheme}://{req.url.host}"
        async with AsyncClient(transport=ASGITransport(app=app), base_url=origin) as inner:
            r = await inner.request(
                req.method,
                req.url.path,
                content=req.content,
                headers={k: v for k, v in req.headers.items() if k.lower() != "host"},
            )
        return HttpxResponse(r.status_code, content=r.content, headers=r.headers)

    return _f


async def _seed(engine: AsyncEngine, tenant_id) -> None:  # type: ignore[no-untyped-def]
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) VALUES (:t, 'acme', 'free', '{}', 30, "
                "'{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"t": str(tenant_id)},
        )


async def _force_flagged(engine: AsyncEngine, tenant_id, actor_hash: str) -> None:  # type: ignore[no-untyped-def]
    async with engine.begin() as conn:
        actor_row = await conn.execute(
            text("SELECT id FROM actor WHERE tenant_id = :t AND external_id_hash = :h"),
            {"t": str(tenant_id), "h": actor_hash},
        )
        actor_id = actor_row.scalar_one()
        await conn.execute(
            text(
                "INSERT INTO suspicion_profile (tenant_id, actor_id, current_score, tier) "
                "VALUES (:t, :a, 80, 4) "
                "ON CONFLICT (tenant_id, actor_id) DO UPDATE SET "
                "current_score = EXCLUDED.current_score, tier = EXCLUDED.tier"
            ),
            {"t": str(tenant_id), "a": str(actor_id)},
        )

    settings = get_settings()
    adapter = QdrantAdapter(
        client=get_qdrant_client(),
        collection_name=settings.qdrant_fingerprint_collection,
        dim=settings.fingerprint_vector_dim,
    )
    await adapter.bootstrap()

    now = datetime.now(UTC)
    since = now - timedelta(days=settings.graph_lookback_days * 10)
    async with tenant_session(tenant_id) as session:
        rows = await fetch_window_rows(session, tenant_id=tenant_id, actor_id=actor_id, since=since)
        window = aggregate_window_from_rows(rows, actor_id=actor_id, now=now)
    fingerprint = compute_fingerprint(window)
    await upsert_fingerprint(
        adapter,
        tenant_id=tenant_id,
        actor_id=actor_id,
        vector=fingerprint,
        flagged=True,
    )


async def test_duplicate_account_fingerprint_match_within_5_messages(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    scenario = yaml.safe_load(_SCENARIO.read_text())
    tenant_id = uuid4()
    await _seed(admin_engine, tenant_id)

    predator_hash = "a" * 64
    duplicate_hash = "b" * 64
    minor_hash = "c" * 64
    base = datetime.now(UTC) - timedelta(days=15)

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

    flagged_by = None
    with respx.mock(assert_all_called=False) as router:
        for host, app in apps.items():
            router.route(host=host).mock(side_effect=_forwarder(app))
        router.route(host="127.0.0.1", port=6333).pass_through()

        async with AsyncClient(
            transport=ASGITransport(app=ingestion), base_url="http://test"
        ) as client:
            for i, msg in enumerate(scenario["training_messages"]):
                ts = base + timedelta(days=msg["day_offset"], hours=msg["hour"])
                await client.post(
                    "/v1/events",
                    json={
                        "idempotency_key": f"train-{i}",
                        "tenant_id": str(tenant_id),
                        "conversation_id": str(uuid4()),
                        "actor_external_id_hash": predator_hash,
                        "target_actor_external_id_hashes": [minor_hash],
                        "event_type": "message",
                        "timestamp": ts.isoformat(),
                        "content": msg["text"],
                        "metadata": {
                            "recipient_age_bands": ["under_13"],
                            "recipient_timezone": "UTC",
                        },
                    },
                )

            await _force_flagged(admin_engine, tenant_id, predator_hash)

            for i, msg in enumerate(scenario["duplicate_messages"]):
                ts = (
                    base
                    + timedelta(days=msg["day_offset"], hours=msg["hour"])
                    + timedelta(minutes=i)
                )
                resp = await client.post(
                    "/v1/events",
                    json={
                        "idempotency_key": f"dup-{i}",
                        "tenant_id": str(tenant_id),
                        "conversation_id": str(uuid4()),
                        "actor_external_id_hash": duplicate_hash,
                        "target_actor_external_id_hashes": [minor_hash],
                        "event_type": "message",
                        "timestamp": ts.isoformat(),
                        "content": msg["text"],
                        "metadata": {
                            "recipient_age_bands": ["under_13"],
                            "recipient_timezone": "UTC",
                        },
                    },
                )
                body = resp.json()
                if any(s["kind"] == "behavioral_fingerprint_match" for s in body["signals"]):
                    flagged_by = i + 1
                    break

    assert flagged_by is not None
    assert flagged_by <= 5
