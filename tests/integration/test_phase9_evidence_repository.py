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
from shared.honeypot.repository import get_evidence_package, persist_evidence_package

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_TENANT_SQL = text(
    "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, data_retention_days, feature_flags) "
    "VALUES (:t, 'x', 'free', '{}', 30, '{}'::jsonb)"
)
_ACTOR_SQL = text(
    "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band, metadata) "
    "VALUES (:a, :t, :h, 'unknown', '{}'::jsonb)"
)


async def test_persist_and_fetch_evidence_package(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    async with admin_engine.begin() as conn:
        await conn.execute(_TENANT_SQL, {"t": str(tenant_id)})
        await conn.execute(_ACTOR_SQL, {"a": str(actor_id), "t": str(tenant_id), "h": "2" * 64})
    pkg = build_evidence_package(
        tenant_id=tenant_id,
        actor_id=actor_id,
        persona_id="emma-13-us-east",
        activated_at=datetime.now(UTC),
        deactivated_at=datetime.now(UTC),
        conversation_excerpts=("actor: hi",),
        pattern_matches=(),
        reasoning_snapshot={},
        activation_audit_trail=(),
    )
    async with tenant_session(tenant_id) as s:
        evidence_id = await persist_evidence_package(s, package=pkg)
    async with tenant_session(tenant_id) as s:
        row = (
            await s.execute(
                select(HoneypotEvidencePackage).where(HoneypotEvidencePackage.id == evidence_id)
            )
        ).scalar_one()
    assert row.content_hash == pkg.content_hash
    assert row.persona_id == "emma-13-us-east"
    async with tenant_session(tenant_id) as s:
        fetched = await get_evidence_package(s, evidence_id=evidence_id)
    assert fetched is not None
    assert fetched.content_hash == pkg.content_hash
