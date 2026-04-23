# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import hashlib
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
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.ingestion.app.main import create_app as create_ingestion
from services.patterns.app.main import create_app as create_patterns
from services.preprocessing.app.main import create_app as create_preprocess
from services.scoring.app.main import create_app as create_scoring
from shared.config import Settings
from shared.db.models import AuditLogEntry, SuspicionProfile
from shared.db.session import tenant_session
from shared.response.mandatory_report import evaluate_mandatory_report
from shared.schemas.enums import Jurisdiction, ResponseTier
from shared.scoring.signals import ScoreSignal, SignalKind

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_SCENARIO = Path(__file__).parents[1] / "fixtures" / "scenarios" / "slow_burn_predator.yaml"
_PILOT_TENANT_ID_STR = "11111111-1111-1111-1111-111111111111"


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


async def test_slow_burn_scenario_reaches_critical_with_mandatory_report(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    pilot_tid = UUID(_PILOT_TENANT_ID_STR)
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                "VALUES (:t, 'Pilot Platform', 'pro', '{US}', 90, '{}'::jsonb) "
                "ON CONFLICT DO NOTHING"
            ),
            {"t": _PILOT_TENANT_ID_STR},
        )

    scenario = yaml.safe_load(_SCENARIO.read_text())
    convs = {c["id"]: (str(uuid4()), c["target_hash"]) for c in scenario["conversations"]}
    actor_hash = hashlib.sha256(b"sentinel_case_study_actor").hexdigest()
    base_time = datetime.now(UTC) - timedelta(days=25)

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
            router.route(host=host).mock(side_effect=_forwarder(app))
        router.route(host="127.0.0.1", port=6333).pass_through()

        async with AsyncClient(
            transport=ASGITransport(app=ingestion), base_url="http://test"
        ) as client:
            for msg in scenario["messages"]:
                idx = msg["idx"]
                conv_uuid, target_hash = convs[msg["conversation_idx"]]
                ts = base_time + timedelta(days=msg["day_offset"], hours=msg["hour"])
                await client.post(
                    "/v1/events",
                    json={
                        "idempotency_key": f"case-study-msg{idx}",
                        "tenant_id": _PILOT_TENANT_ID_STR,
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

    async with tenant_session(pilot_tid) as session:
        profiles = (await session.execute(select(SuspicionProfile))).scalars().all()

    assert len(profiles) == 1, "exactly one actor profile expected"
    profile = profiles[0]
    assert profile.tier == ResponseTier.CRITICAL, (
        f"actor must reach CRITICAL (tier 5), got tier {profile.tier}"
    )

    mandatory_report_pkg = evaluate_mandatory_report(
        tenant_id=pilot_tid,
        actor_id=profile.actor_id,
        tier=ResponseTier(profile.tier),
        jurisdictions=(Jurisdiction.US,),
        signals=(
            ScoreSignal(kind=SignalKind.SECRECY_REQUEST, confidence=0.95),
            ScoreSignal(kind=SignalKind.PHOTO_REQUEST, confidence=0.90),
        ),
    )
    assert mandatory_report_pkg is not None, (
        "mandatory_report package must be evaluable for CRITICAL actor with triggering signals"
    )
    assert mandatory_report_pkg.report_template == "NCMEC_CYBERTIPLINE"

    async with tenant_session(pilot_tid) as session:
        tier_change_events = (
            (
                await session.execute(
                    select(AuditLogEntry).where(AuditLogEntry.event_type == "tier.changed")
                )
            )
            .scalars()
            .all()
        )

    assert len(tier_change_events) >= 1, "at least one tier.changed audit event must be recorded"
    final_tiers = [e.details.get("new_tier") for e in tier_change_events]
    assert ResponseTier.CRITICAL in final_tiers, (
        f"tier.changed events must include CRITICAL escalation, got: {final_tiers}"
    )
