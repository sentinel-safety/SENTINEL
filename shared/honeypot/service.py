# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from shared.audit.events import (
    record_honeypot_activated,
    record_honeypot_denied,
    record_honeypot_evidence_packaged,
)
from shared.honeypot.activation import ActivationDecision, evaluate_activation
from shared.honeypot.evidence import build_evidence_package
from shared.honeypot.personas import PersonaLoader
from shared.honeypot.prompt import build_steering_prompt
from shared.honeypot.repository import persist_evidence_package, record_activation
from shared.llm.provider import LLMProvider
from shared.schemas.enums import Jurisdiction

_REPLY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"reply": {"type": "string", "maxLength": 500}},
    "required": ["reply"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class HoneypotContext:
    actor_tier: int
    tenant_feature_flags: dict[str, bool]
    tenant_jurisdictions: tuple[Jurisdiction, ...]
    jurisdiction_allowlist: tuple[Jurisdiction, ...]
    persona_id: str
    persona_loader: PersonaLoader
    conversation_excerpt: tuple[str, ...]
    provider: LLMProvider
    tier_threshold: int


@dataclass(frozen=True)
class HoneypotDenied:
    decision: ActivationDecision


@dataclass(frozen=True)
class HoneypotResult:
    reply: str
    persona_id: str
    prompt_version: str
    decision: ActivationDecision


async def invoke_honeypot(ctx: HoneypotContext) -> HoneypotDenied | HoneypotResult:
    persona = ctx.persona_loader.get(ctx.persona_id)
    decision = evaluate_activation(
        actor_tier=ctx.actor_tier,
        tenant_feature_flags=ctx.tenant_feature_flags,
        tenant_jurisdictions=ctx.tenant_jurisdictions,
        jurisdiction_allowlist=ctx.jurisdiction_allowlist,
        persona_activation_scope=persona.activation_scope,
        tier_threshold=ctx.tier_threshold,
    )
    if not decision.allowed:
        return HoneypotDenied(decision=decision)
    prompt = build_steering_prompt(persona=persona, conversation_excerpt=ctx.conversation_excerpt)
    response = await ctx.provider.complete(prompt=prompt, schema=_REPLY_SCHEMA)
    return HoneypotResult(
        reply=str(response["reply"]),
        persona_id=persona.id,
        prompt_version=persona.prompt_version,
        decision=decision,
    )


async def invoke_and_persist(
    session: AsyncSession,
    *,
    ctx: HoneypotContext,
    tenant_id: UUID,
    actor_id: UUID,
    now: datetime,
    pattern_matches: tuple[dict[str, object], ...] = (),
    reasoning_snapshot: dict[str, object] | None = None,
) -> HoneypotDenied | HoneypotResult:
    activation_id = uuid4()
    outcome = await invoke_honeypot(ctx)
    if isinstance(outcome, HoneypotDenied):
        await record_activation(
            session,
            tenant_id=tenant_id,
            actor_id=actor_id,
            persona_id=None,
            activated_at=now,
            deactivated_at=None,
            decision="deny",
            reasons=outcome.decision.reasons,
            evidence_package_id=None,
        )
        await record_honeypot_denied(
            session,
            tenant_id=tenant_id,
            actor_id=actor_id,
            reasons=outcome.decision.reasons,
            activation_id=activation_id,
            timestamp=now,
        )
        return outcome

    await record_honeypot_activated(
        session,
        tenant_id=tenant_id,
        actor_id=actor_id,
        persona_id=outcome.persona_id,
        activation_id=activation_id,
        timestamp=now,
    )
    package = build_evidence_package(
        tenant_id=tenant_id,
        actor_id=actor_id,
        persona_id=outcome.persona_id,
        activated_at=now,
        deactivated_at=now,
        conversation_excerpts=(*ctx.conversation_excerpt, f"persona: {outcome.reply}"),
        pattern_matches=pattern_matches,
        reasoning_snapshot=reasoning_snapshot or {},
        activation_audit_trail=(f"activation_id:{activation_id}",),
    )
    evidence_id = await persist_evidence_package(session, package=package)
    await record_activation(
        session,
        tenant_id=tenant_id,
        actor_id=actor_id,
        persona_id=outcome.persona_id,
        activated_at=now,
        deactivated_at=now,
        decision="allow",
        reasons=(),
        evidence_package_id=evidence_id,
    )
    await record_honeypot_evidence_packaged(
        session,
        tenant_id=tenant_id,
        actor_id=actor_id,
        evidence_package_id=evidence_id,
        content_hash=package.content_hash,
        activation_id=activation_id,
        timestamp=now,
    )
    return outcome
