# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine

from shared.db.models import HoneypotEvidencePackage
from shared.db.session import tenant_session
from shared.honeypot.evidence import build_evidence_package
from shared.honeypot.repository import persist_evidence_package

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_TENANT_SQL = text(
    "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, data_retention_days, feature_flags) "
    "VALUES (:t, 'x', 'free', '{}', 30, '{}'::jsonb)"
)
_ACTOR_SQL = text(
    "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band, metadata) "
    "VALUES (:a, :t, :h, 'unknown', '{}'::jsonb)"
)


async def test_tenant_cannot_read_other_tenants_evidence(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    tenant_a = uuid4()
    tenant_b = uuid4()
    actor_a = uuid4()
    actor_b = uuid4()
    async with admin_engine.begin() as conn:
        for t in (tenant_a, tenant_b):
            await conn.execute(_TENANT_SQL, {"t": str(t)})
        await conn.execute(_ACTOR_SQL, {"a": str(actor_a), "t": str(tenant_a), "h": "4" * 64})
        await conn.execute(_ACTOR_SQL, {"a": str(actor_b), "t": str(tenant_b), "h": "5" * 64})
    pkg_a = build_evidence_package(
        tenant_id=tenant_a,
        actor_id=actor_a,
        persona_id="emma",
        activated_at=datetime.now(UTC),
        deactivated_at=datetime.now(UTC),
        conversation_excerpts=("actor:a",),
        pattern_matches=(),
        reasoning_snapshot={},
        activation_audit_trail=(),
    )
    async with tenant_session(tenant_a) as s:
        await persist_evidence_package(s, package=pkg_a)
    async with tenant_session(tenant_b) as s:
        rows = (await s.execute(select(HoneypotEvidencePackage))).scalars().all()
    assert rows == []
