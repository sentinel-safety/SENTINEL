# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.honeypot.app.main import create_app
from shared.config.settings import Settings
from shared.db.session import tenant_session
from shared.schemas.enums import Jurisdiction

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def _settings_with_personas(personas_dir: Path) -> Settings:
    return Settings(
        honeypot_personas_dir=str(personas_dir),
        honeypot_jurisdiction_allowlist=(Jurisdiction.US,),
    )


def _write_persona(d: Path, pid: str = "emma") -> None:
    (d / f"{pid}.yaml").write_text(
        f"id: {pid}\nage: 13\ngender: female\nlocation: us-east\n"
        "interests: [art]\nvocabulary_level: age_typical\nregional_speech: us_east_suburban\n"
        'consent_statement: "SYNTHETIC — not a real child"\n'
        "activation_scope: [US]\nprompt_version: v1\n",
        encoding="utf-8",
    )


async def _seed(
    admin_engine: AsyncEngine, tenant_id: object, actor_id: object, *, flags: str
) -> None:
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, data_retention_days, compliance_jurisdictions, feature_flags) "
                "VALUES (:t, 'x', 'free', 30, :j, CAST(:f AS jsonb))"
            ),
            {"t": str(tenant_id), "j": ["US"], "f": flags},
        )
        await conn.execute(
            text(
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band) "
                "VALUES (:a, :t, :h, 'unknown')"
            ),
            {"a": str(actor_id), "t": str(tenant_id), "h": "6" * 64},
        )


async def test_evaluate_denies_when_feature_flag_off(
    clean_tables: None, admin_engine: AsyncEngine, tmp_path: Path
) -> None:
    _write_persona(tmp_path)
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed(
        admin_engine,
        tenant_id,
        actor_id,
        flags='{"honeypot_enabled": false, "honeypot_legal_review_acknowledged": false}',
    )
    app = create_app(_settings_with_personas(tmp_path))
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
            r = await client.post(
                "/internal/honeypot/evaluate",
                json={
                    "tenant_id": str(tenant_id),
                    "actor_id": str(actor_id),
                    "actor_tier": 4,
                    "persona_id": "emma",
                    "conversation_excerpt": [],
                    "pattern_matches": [],
                    "reasoning_snapshot": {},
                },
            )
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "deny"
    assert "feature_flag_disabled" in body["reasons"]


async def test_evaluate_allows_when_all_gates_pass_and_evidence_fetchable(
    clean_tables: None, admin_engine: AsyncEngine, tmp_path: Path
) -> None:
    _write_persona(tmp_path)
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed(
        admin_engine,
        tenant_id,
        actor_id,
        flags='{"honeypot_enabled": true, "honeypot_legal_review_acknowledged": true}',
    )
    app = create_app(_settings_with_personas(tmp_path))

    class _StubProvider:
        async def complete(self, *, prompt: str, schema: object) -> dict[str, str]:
            return {"reply": "hey"}

    app.state.llm_provider = _StubProvider()
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
            r = await client.post(
                "/internal/honeypot/evaluate",
                json={
                    "tenant_id": str(tenant_id),
                    "actor_id": str(actor_id),
                    "actor_tier": 4,
                    "persona_id": "emma",
                    "conversation_excerpt": ["actor: hi"],
                    "pattern_matches": [{"pattern_name": "secrecy_request"}],
                    "reasoning_snapshot": {"new_tier": "restrict"},
                },
            )
            assert r.status_code == 200
            body = r.json()
            assert body["decision"] == "allow"
            assert body["synthetic_header"] == "X-Sentinel-Honeypot: synthetic"
            async with tenant_session(tenant_id) as s:
                row = (
                    await s.execute(
                        text(
                            "SELECT id FROM honeypot_evidence_package "
                            "ORDER BY created_at DESC LIMIT 1"
                        )
                    )
                ).one()
            r2 = await client.get(
                f"/internal/honeypot/evidence/{row.id}",
                headers={"X-Tenant-Id": str(tenant_id)},
            )
            assert r2.status_code == 200
            detail = r2.json()
            assert detail["persona_id"] == "emma"
            assert detail["synthetic_persona"] is True
