# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from shared.db.session import tenant_session
from shared.honeypot.personas import PersonaLoader
from shared.honeypot.service import HoneypotContext, HoneypotDenied, invoke_and_persist
from shared.schemas.enums import Jurisdiction
from tests.fixtures.phase9_redteam.scenarios import ALL_SCENARIOS, Scenario

pytestmark = [pytest.mark.integration, pytest.mark.honeypot, pytest.mark.asyncio]

_REDTEAM_SIGNALS = (
    "secret",
    "don't tell",
    "move off",
    "snap",
    "discord",
    "telegram",
    "venmo",
    "address",
    "school name",
    "selfie",
    "webcam",
    "alone",
    "boyfriend",
    "meet irl",
    "come over",
    "kissed",
    "wear to bed",
    "phone number",
    "new account",
    "body",
    "special connection",
    "don't post",
    "delete these",
    "uniform",
    "you're older",
    "real phone",
    "mature for your age",
    "don't understand you",
    "tell me anything",
    "only person who gets me",
    "time do you go to sleep",
    "just our thing",
    "you deserve better",
)


class _ScriptedProvider:
    async def complete(self, *, prompt: str, schema: object) -> dict[str, str]:
        return {"reply": "idk, what do you mean?"}


def _confirms_predator(scenario: Scenario) -> bool:
    joined = " ".join(scenario.conversation).lower()
    return any(signal in joined for signal in _REDTEAM_SIGNALS)


async def _seed(admin_engine: AsyncEngine, tenant_id: object, actor_id: object) -> None:
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, data_retention_days, compliance_jurisdictions, feature_flags) "
                "VALUES (:t, 'x', 'free', 30, :j, CAST(:f AS jsonb))"
            ),
            {
                "t": str(tenant_id),
                "j": ["US"],
                "f": '{"honeypot_enabled": true, "honeypot_legal_review_acknowledged": true}',
            },
        )
        await conn.execute(
            text(
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band) "
                "VALUES (:a, :t, :h, 'unknown')"
            ),
            {"a": str(actor_id), "t": str(tenant_id), "h": "8" * 64},
        )


async def _run_scenario(
    admin_engine: AsyncEngine, tmp_path: Path, scenario: Scenario
) -> Literal["confirmed_predator", "cleared"]:
    personas = tmp_path / "p"
    personas.mkdir(exist_ok=True)
    (personas / "emma.yaml").write_text(
        "id: emma\nage: 13\ngender: female\nlocation: us-east\n"
        "interests: [art]\nvocabulary_level: age_typical\nregional_speech: us_east_suburban\n"
        'consent_statement: "SYNTHETIC — not a real child"\n'
        "activation_scope: [US]\nprompt_version: v1\n",
        encoding="utf-8",
    )
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed(admin_engine, tenant_id, actor_id)
    ctx = HoneypotContext(
        actor_tier=scenario.actor_tier,
        tenant_feature_flags={
            "honeypot_enabled": True,
            "honeypot_legal_review_acknowledged": True,
        },
        tenant_jurisdictions=(Jurisdiction.US,),
        jurisdiction_allowlist=(Jurisdiction.US,),
        persona_id="emma",
        persona_loader=PersonaLoader(personas),
        conversation_excerpt=scenario.conversation,
        provider=_ScriptedProvider(),
        tier_threshold=4,
    )
    async with tenant_session(tenant_id) as s:
        outcome = await invoke_and_persist(
            s,
            ctx=ctx,
            tenant_id=tenant_id,
            actor_id=actor_id,
            now=datetime.now(UTC),
        )
    if isinstance(outcome, HoneypotDenied):
        return "cleared"
    return "confirmed_predator" if _confirms_predator(scenario) else "cleared"


async def test_redteam_acceptance_bar(
    clean_tables: None, admin_engine: AsyncEngine, tmp_path: Path
) -> None:
    tp = fn = fp = tn = 0
    for sc in ALL_SCENARIOS:
        verdict = await _run_scenario(admin_engine, tmp_path, sc)
        if sc.label == "predator":
            if verdict == "confirmed_predator":
                tp += 1
            else:
                fn += 1
        else:
            if verdict == "confirmed_predator":
                fp += 1
            else:
                tn += 1
    assert fp == 0, f"False positives forbidden; saw {fp} (tp={tp}, fn={fn}, tn={tn})"
    tp_rate = tp / (tp + fn)
    assert tp_rate >= 0.90, f"TP rate {tp_rate:.2f} < 0.90 (tp={tp}, fn={fn})"
