# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from services.honeypot.app.schemas import (
    EvaluateRequest,
    EvaluateResponseAllowed,
    EvaluateResponseDenied,
    EvidenceResponse,
)
from shared.db.models import Tenant
from shared.db.session import tenant_session
from shared.honeypot.repository import get_evidence_package
from shared.honeypot.service import (
    HoneypotContext,
    HoneypotDenied,
    HoneypotResult,
    invoke_and_persist,
)
from shared.llm.factory import build_llm_provider
from shared.schemas.enums import Jurisdiction

router = APIRouter()


def _jurisdiction_tuple(raw: list[str] | None) -> tuple[Jurisdiction, ...]:
    return tuple(Jurisdiction(x) for x in raw or ())


@router.post("/internal/honeypot/evaluate")
async def evaluate(
    payload: EvaluateRequest, request: Request
) -> EvaluateResponseAllowed | EvaluateResponseDenied:
    settings = request.app.state.settings
    persona_loader = request.app.state.persona_loader
    provider = getattr(request.app.state, "llm_provider", None) or build_llm_provider(settings)
    async with tenant_session(payload.tenant_id) as session:
        from sqlalchemy import select

        tenant = (
            await session.execute(select(Tenant).where(Tenant.id == payload.tenant_id))
        ).scalar_one_or_none()
        if tenant is None:
            raise HTTPException(status_code=404, detail="tenant not found")
        ctx = HoneypotContext(
            actor_tier=payload.actor_tier,
            tenant_feature_flags=dict(tenant.feature_flags or {}),
            tenant_jurisdictions=_jurisdiction_tuple(tenant.compliance_jurisdictions),
            jurisdiction_allowlist=tuple(settings.honeypot_jurisdiction_allowlist),
            persona_id=payload.persona_id,
            persona_loader=persona_loader,
            conversation_excerpt=tuple(payload.conversation_excerpt),
            provider=provider,
            tier_threshold=settings.honeypot_tier_threshold,
        )
        outcome = await invoke_and_persist(
            session,
            ctx=ctx,
            tenant_id=payload.tenant_id,
            actor_id=payload.actor_id,
            now=datetime.now(UTC),
            pattern_matches=tuple(payload.pattern_matches),
            reasoning_snapshot=payload.reasoning_snapshot,
        )
    if isinstance(outcome, HoneypotDenied):
        return EvaluateResponseDenied(reasons=outcome.decision.reasons)
    assert isinstance(outcome, HoneypotResult)
    return EvaluateResponseAllowed(
        reply=outcome.reply,
        persona_id=outcome.persona_id,
        prompt_version=outcome.prompt_version,
    )


@router.get("/internal/honeypot/evidence/{evidence_id}")
async def fetch_evidence(evidence_id: UUID, request: Request) -> EvidenceResponse:
    tenant_id_raw = request.headers.get("X-Tenant-Id")
    if not tenant_id_raw:
        raise HTTPException(status_code=400, detail="X-Tenant-Id header required")
    tenant_id = UUID(tenant_id_raw)
    async with tenant_session(tenant_id) as session:
        row = await get_evidence_package(session, evidence_id=evidence_id)
    if row is None:
        raise HTTPException(status_code=404, detail="evidence package not found")
    return EvidenceResponse(
        id=row.id,
        tenant_id=row.tenant_id,
        actor_id=row.actor_id,
        persona_id=row.persona_id,
        content_hash=row.content_hash,
        created_at=row.created_at,
        json_payload=dict(row.json_payload),
    )
