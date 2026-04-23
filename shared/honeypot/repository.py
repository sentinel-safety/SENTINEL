# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models import HoneypotActivationLog, HoneypotEvidencePackage
from shared.honeypot.evidence import EvidencePackage


async def persist_evidence_package(session: AsyncSession, *, package: EvidencePackage) -> UUID:
    row = HoneypotEvidencePackage(
        tenant_id=package.tenant_id,
        actor_id=package.actor_id,
        persona_id=package.persona_id,
        content_hash=package.content_hash,
        json_payload=json.loads(package.json_payload),
    )
    session.add(row)
    await session.flush()
    return row.id


async def record_activation(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    actor_id: UUID,
    persona_id: str | None,
    activated_at: datetime,
    deactivated_at: datetime | None,
    decision: str,
    reasons: tuple[str, ...],
    evidence_package_id: UUID | None,
) -> UUID:
    row = HoneypotActivationLog(
        tenant_id=tenant_id,
        actor_id=actor_id,
        persona_id=persona_id,
        activated_at=activated_at,
        deactivated_at=deactivated_at,
        decision=decision,
        decision_reasons=list(reasons),
        evidence_package_id=evidence_package_id,
    )
    session.add(row)
    await session.flush()
    return row.id


async def get_evidence_package(
    session: AsyncSession, *, evidence_id: UUID
) -> HoneypotEvidencePackage | None:
    result = await session.execute(
        select(HoneypotEvidencePackage).where(HoneypotEvidencePackage.id == evidence_id)
    )
    return result.scalar_one_or_none()
