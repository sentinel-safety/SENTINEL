# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine

from shared.db.models import HoneypotActivationLog
from shared.db.session import tenant_session
from shared.honeypot.evidence import build_evidence_package
from shared.honeypot.repository import persist_evidence_package, record_activation

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_TENANT_SQL = text(
    "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, data_retention_days, feature_flags) "
    "VALUES (:t, 'x', 'free', '{}', 30, '{}'::jsonb)"
)
_ACTOR_SQL = text(
    "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band, metadata) "
    "VALUES (:a, :t, :h, 'unknown', '{}'::jsonb)"
)


async def test_record_activation_deny(clean_tables: None, admin_engine: AsyncEngine) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    async with admin_engine.begin() as conn:
        await conn.execute(_TENANT_SQL, {"t": str(tenant_id)})
        await conn.execute(_ACTOR_SQL, {"a": str(actor_id), "t": str(tenant_id), "h": "0" * 64})
    async with tenant_session(tenant_id) as s:
        activation_id = await record_activation(
            s,
            tenant_id=tenant_id,
            actor_id=actor_id,
            persona_id=None,
            activated_at=datetime.now(UTC),
            deactivated_at=None,
            decision="deny",
            reasons=("tier_below_threshold",),
            evidence_package_id=None,
        )
    async with tenant_session(tenant_id) as s:
        row = (
            await s.execute(
                select(HoneypotActivationLog).where(HoneypotActivationLog.id == activation_id)
            )
        ).scalar_one()
    assert row.decision == "deny"
    assert row.decision_reasons == ["tier_below_threshold"]


async def test_record_activation_allow_with_evidence(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    async with admin_engine.begin() as conn:
        await conn.execute(_TENANT_SQL, {"t": str(tenant_id)})
        await conn.execute(_ACTOR_SQL, {"a": str(actor_id), "t": str(tenant_id), "h": "1" * 64})
    activated = datetime.now(UTC)
    pkg = build_evidence_package(
        tenant_id=tenant_id,
        actor_id=actor_id,
        persona_id="emma-13-us-east",
        activated_at=activated,
        deactivated_at=activated + timedelta(minutes=5),
        conversation_excerpts=("actor: hi",),
        pattern_matches=({"pattern_name": "secrecy_request"},),
        reasoning_snapshot={"new_tier": "restrict"},
        activation_audit_trail=("a",),
    )
    async with tenant_session(tenant_id) as s:
        evidence_id = await persist_evidence_package(s, package=pkg)
    async with tenant_session(tenant_id) as s:
        activation_id = await record_activation(
            s,
            tenant_id=tenant_id,
            actor_id=actor_id,
            persona_id="emma-13-us-east",
            activated_at=activated,
            deactivated_at=activated + timedelta(minutes=5),
            decision="allow",
            reasons=(),
            evidence_package_id=evidence_id,
        )
    async with tenant_session(tenant_id) as s:
        row = (
            await s.execute(
                select(HoneypotActivationLog).where(HoneypotActivationLog.id == activation_id)
            )
        ).scalar_one()
    assert row.decision == "allow"
    assert row.evidence_package_id == evidence_id
