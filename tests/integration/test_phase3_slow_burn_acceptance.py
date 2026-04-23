# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

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
from services.preprocessing.app.main import create_app as create_preprocess
from services.scoring.app.main import create_app as create_scoring
from shared.config import Settings
from shared.schemas.enums import ResponseTier

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_SCENARIO = Path(__file__).parents[1] / "fixtures" / "scenarios" / "slow_burn_predator.yaml"


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


async def test_slow_burn_predator_scenario_hits_tier_progression(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    scenario = yaml.safe_load(_SCENARIO.read_text())
    messages = scenario["messages"]
    convs = {c["id"]: (str(uuid4()), c["target_hash"]) for c in scenario["conversations"]}
    checkpoints = {cp["after_idx"]: cp["min_tier"] for cp in scenario["tier_checkpoints"]}

    tenant_id = uuid4()
    await _seed(admin_engine, tenant_id)
    actor_hash = "a" * 64

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

    base = datetime.now(UTC) - timedelta(days=25)
    last_tier_value = 0
    last_score = 0
    with respx.mock(assert_all_called=False) as router:
        for host, app in apps.items():
            router.route(host=host).mock(side_effect=_forwarder(app))
        router.route(host="127.0.0.1", port=6333).pass_through()
        async with AsyncClient(
            transport=ASGITransport(app=ingestion), base_url="http://test"
        ) as client:
            for msg in messages:
                idx = msg["idx"]
                conv_uuid, target_hash = convs[msg["conversation_idx"]]
                ts = base + timedelta(days=msg["day_offset"], hours=msg["hour"])
                resp = await client.post(
                    "/v1/events",
                    json={
                        "idempotency_key": f"slow-burn-{idx}",
                        "tenant_id": str(tenant_id),
                        "conversation_id": conv_uuid,
                        "actor_external_id_hash": actor_hash,
                        "target_actor_external_id_hashes": [target_hash],
                        "event_type": "message",
                        "timestamp": ts.isoformat(),
                        "content": msg["text"],
                        "metadata": {
                            "recipient_age_bands": ["under_13"],
                            "recipient_timezone": "UTC",
                        },
                    },
                )
                assert resp.status_code == 200, f"msg {idx} failed: {resp.text}"
                body = resp.json()
                last_score = body["current_score"]
                last_tier_value = ResponseTier[body["tier"].upper()].value
                if idx in checkpoints:
                    required = checkpoints[idx]
                    assert last_tier_value >= required, (
                        f"after msg {idx}: tier value={last_tier_value} < required={required} "
                        f"(score={last_score})"
                    )
    assert last_score >= scenario["expected_final_score_min"]
    assert last_tier_value >= scenario["expected_final_tier_min"]
