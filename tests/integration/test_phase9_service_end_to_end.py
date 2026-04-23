# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine

from shared.db.models import (
    AuditLogEntry,
    HoneypotActivationLog,
    HoneypotEvidencePackage,
)
from shared.db.session import tenant_session
from shared.honeypot.personas import PersonaLoader
from shared.honeypot.service import (
    HoneypotContext,
    HoneypotDenied,
    HoneypotResult,
    invoke_and_persist,
)
from shared.schemas.enums import Jurisdiction

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_TENANT_SQL = text(
    "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, data_retention_days, feature_flags) "
    "VALUES (:t, 'x', 'free', :j, 30, '{}'::jsonb)"
)
_ACTOR_SQL = text(
    "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band, metadata) "
    "VALUES (:a, :t, :h, 'unknown', '{}'::jsonb)"
)


class _StubProvider:
    def __init__(self, reply: str) -> None:
        self.reply = reply

    async def complete(self, *, prompt: str, schema: object) -> dict[str, object]:
        return {"reply": self.reply}


def _persona_dir(tmp_path: Path) -> Path:
    (tmp_path / "emma.yaml").write_text(
        "id: emma\nage: 13\ngender: female\nlocation: us-east\n"
        "interests: [art]\nvocabulary_level: age_typical\nregional_speech: us_east_suburban\n"
        'consent_statement: "SYNTHETIC — not a real child"\n'
        "activation_scope: [US]\nprompt_version: v1\n",
        encoding="utf-8",
    )
    return tmp_path


async def _seed_tenant_actor(
    admin_engine: AsyncEngine, tenant_id: object, actor_id: object, jurisdictions: list[str]
) -> None:
    async with admin_engine.begin() as conn:
        await conn.execute(_TENANT_SQL, {"t": str(tenant_id), "j": jurisdictions})
        await conn.execute(_ACTOR_SQL, {"a": str(actor_id), "t": str(tenant_id), "h": "3" * 64})


async def test_deny_path_writes_audit_and_log_no_evidence(
    clean_tables: None, admin_engine: AsyncEngine, tmp_path: Path
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed_tenant_actor(admin_engine, tenant_id, actor_id, ["US"])
    ctx = HoneypotContext(
        actor_tier=0,
        tenant_feature_flags={
            "honeypot_enabled": False,
            "honeypot_legal_review_acknowledged": False,
        },
        tenant_jurisdictions=(Jurisdiction.US,),
        jurisdiction_allowlist=(),
        persona_id="emma",
        persona_loader=PersonaLoader(_persona_dir(tmp_path)),
        conversation_excerpt=(),
        provider=_StubProvider("hi"),
        tier_threshold=4,
    )
    async with tenant_session(tenant_id) as s:
        result = await invoke_and_persist(
            s, ctx=ctx, tenant_id=tenant_id, actor_id=actor_id, now=datetime.now(UTC)
        )
    assert isinstance(result, HoneypotDenied)
    async with tenant_session(tenant_id) as s:
        logs = (await s.execute(select(HoneypotActivationLog))).scalars().all()
        audits = (
            (
                await s.execute(
                    select(AuditLogEntry).where(AuditLogEntry.event_type == "honeypot.denied")
                )
            )
            .scalars()
            .all()
        )
        evidence = (await s.execute(select(HoneypotEvidencePackage))).scalars().all()
    assert len(logs) == 1
    assert logs[0].decision == "deny"
    assert len(audits) == 1
    assert evidence == []


async def test_allow_path_writes_audit_log_evidence_and_activation_link(
    clean_tables: None, admin_engine: AsyncEngine, tmp_path: Path
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed_tenant_actor(admin_engine, tenant_id, actor_id, ["US"])
    ctx = HoneypotContext(
        actor_tier=4,
        tenant_feature_flags={"honeypot_enabled": True, "honeypot_legal_review_acknowledged": True},
        tenant_jurisdictions=(Jurisdiction.US,),
        jurisdiction_allowlist=(Jurisdiction.US,),
        persona_id="emma",
        persona_loader=PersonaLoader(_persona_dir(tmp_path)),
        conversation_excerpt=("actor: hi",),
        provider=_StubProvider("hey"),
        tier_threshold=4,
    )
    async with tenant_session(tenant_id) as s:
        result = await invoke_and_persist(
            s, ctx=ctx, tenant_id=tenant_id, actor_id=actor_id, now=datetime.now(UTC)
        )
    assert isinstance(result, HoneypotResult)
    async with tenant_session(tenant_id) as s:
        logs = (await s.execute(select(HoneypotActivationLog))).scalars().all()
        evidence = (await s.execute(select(HoneypotEvidencePackage))).scalars().all()
        audits = (
            (
                await s.execute(
                    select(AuditLogEntry).where(
                        AuditLogEntry.event_type.in_(
                            (
                                "honeypot.activated",
                                "honeypot.evidence_packaged",
                            )
                        )
                    )
                )
            )
            .scalars()
            .all()
        )
    assert len(logs) == 1
    assert logs[0].decision == "allow"
    assert len(evidence) == 1
    assert logs[0].evidence_package_id == evidence[0].id
    assert {a.event_type for a in audits} == {
        "honeypot.activated",
        "honeypot.evidence_packaged",
    }
