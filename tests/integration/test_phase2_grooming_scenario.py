# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
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

_SCENARIO = Path(__file__).parents[1] / "fixtures" / "scenarios" / "grooming_30msg.yaml"


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


async def _seed_tenant(engine: AsyncEngine, tenant_id: UUID) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                "VALUES (:tid, 'acme', 'free', '{}', 30, '{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"tid": str(tenant_id)},
        )


def _build_apps(settings: Settings) -> dict[str, Any]:
    return {
        "preprocess": create_preprocess(settings),
        "patterns": create_patterns(settings),
        "score": create_scoring(settings),
    }


async def test_grooming_scenario_30_messages_escalates_through_tiers(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    scenario = yaml.safe_load(_SCENARIO.read_text())
    messages = scenario["messages"]
    checkpoints = {cp["after_idx"]: cp["min_tier"] for cp in scenario["tier_checkpoints"]}

    tenant_id = uuid4()
    await _seed_tenant(admin_engine, tenant_id)

    actor_hash = "a" * 64
    conversation_id = str(uuid4())

    settings = Settings(
        env="test",
        preprocess_base_url="http://preprocess",
        patterns_base_url="http://patterns",
        scoring_base_url="http://score",
    )
    apps = _build_apps(settings)
    ingestion = create_ingestion(settings)

    with respx.mock(assert_all_called=False) as router:
        for host, app in apps.items():
            router.route(host=host).mock(side_effect=_asgi_forwarder(app))
        router.route(host="127.0.0.1", port=6333).pass_through()

        async with AsyncClient(
            transport=ASGITransport(app=ingestion), base_url="http://test"
        ) as client:
            score = 0
            for msg in messages:
                idx = msg["idx"]
                resp = await client.post(
                    "/v1/events",
                    json={
                        "idempotency_key": f"scenario-msg-{idx}",
                        "tenant_id": str(tenant_id),
                        "conversation_id": conversation_id,
                        "actor_external_id_hash": actor_hash,
                        "target_actor_external_id_hashes": ["b" * 64],
                        "event_type": "message",
                        "timestamp": f"2026-04-19T10:{idx:02d}:00+00:00",
                        "content": msg["text"],
                        "metadata": {
                            "recipient_age_bands": ["under_13"],
                            "recipient_timezone": "UTC",
                        },
                    },
                )
                assert resp.status_code == 200, f"msg {idx} failed: {resp.text}"
                body = resp.json()
                score = body["current_score"]

                if idx in checkpoints:
                    min_tier_value = checkpoints[idx]
                    actual_tier_value = ResponseTier[body["tier"].upper()].value
                    assert actual_tier_value >= min_tier_value, (
                        f"after msg {idx}: tier={body['tier']} (value={actual_tier_value}) "
                        f"< required={min_tier_value}, score={score}"
                    )

    assert score >= scenario["expected_final_score_min"], (
        f"final score {score} < expected minimum {scenario['expected_final_score_min']}"
    )
    assert ResponseTier[body["tier"].upper()].value >= scenario["expected_final_tier_min"], (
        f"final tier {body['tier']} below expected minimum {scenario['expected_final_tier_min']}"
    )


async def test_grooming_scenario_watch_tier_reached_by_first_secrecy_signal(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    await _seed_tenant(admin_engine, tenant_id)

    settings = Settings(
        env="test",
        preprocess_base_url="http://preprocess",
        patterns_base_url="http://patterns",
        scoring_base_url="http://score",
    )
    apps = _build_apps(settings)
    ingestion = create_ingestion(settings)

    with respx.mock(assert_all_called=False) as router:
        for host, app in apps.items():
            router.route(host=host).mock(side_effect=_asgi_forwarder(app))
        router.route(host="127.0.0.1", port=6333).pass_through()

        async with AsyncClient(
            transport=ASGITransport(app=ingestion), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/v1/events",
                json={
                    "idempotency_key": "scenario-watch-1",
                    "tenant_id": str(tenant_id),
                    "conversation_id": str(uuid4()),
                    "actor_external_id_hash": "c" * 64,
                    "target_actor_external_id_hashes": ["d" * 64],
                    "event_type": "message",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "content": "don't tell your parents about me",
                    "metadata": {
                        "recipient_age_bands": ["under_13"],
                        "recipient_timezone": "UTC",
                    },
                },
            )

    assert resp.status_code == 200
    body = resp.json()
    assert ResponseTier[body["tier"].upper()].value >= ResponseTier.WATCH.value
    assert any(s["kind"] == "secrecy_request" for s in body["signals"])


async def test_grooming_scenario_gift_offering_vbucks_flagged(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    await _seed_tenant(admin_engine, tenant_id)

    settings = Settings(
        env="test",
        preprocess_base_url="http://preprocess",
        patterns_base_url="http://patterns",
        scoring_base_url="http://score",
    )
    apps = _build_apps(settings)
    ingestion = create_ingestion(settings)

    with respx.mock(assert_all_called=False) as router:
        for host, app in apps.items():
            router.route(host=host).mock(side_effect=_asgi_forwarder(app))
        router.route(host="127.0.0.1", port=6333).pass_through()

        async with AsyncClient(
            transport=ASGITransport(app=ingestion), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/v1/events",
                json={
                    "idempotency_key": "scenario-gift-vbucks",
                    "tenant_id": str(tenant_id),
                    "conversation_id": str(uuid4()),
                    "actor_external_id_hash": "e" * 64,
                    "target_actor_external_id_hashes": ["f" * 64],
                    "event_type": "message",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "content": "i'll give you v-bucks if you keep talking to me",
                    "metadata": {
                        "recipient_age_bands": ["under_13"],
                        "recipient_timezone": "UTC",
                    },
                },
            )

    assert resp.status_code == 200
    body = resp.json()
    gift_signals = [s for s in body["signals"] if s["kind"] == "gift_offering"]
    assert len(gift_signals) >= 1, (
        "v-bucks gift offering must be flagged by rule; LLM second pass may refine confidence"
    )
