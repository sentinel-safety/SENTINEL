# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from shared.schemas.base import FrozenModel, UtcDatetime

_CONTENT_MARKER = "SYNTHETIC PERSONA — evidence collected with AI decoy"


class EvidencePackage(FrozenModel):
    tenant_id: UUID
    actor_id: UUID
    persona_id: str = Field(min_length=1, max_length=64)
    activated_at: UtcDatetime
    deactivated_at: UtcDatetime
    conversation_excerpts: tuple[str, ...]
    pattern_matches: tuple[dict[str, Any], ...]
    reasoning_snapshot: dict[str, Any]
    activation_audit_trail: tuple[str, ...]
    synthetic_persona: bool = True
    content_marker: str = _CONTENT_MARKER
    json_payload: str
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


def _payload_dict(
    *,
    tenant_id: UUID,
    actor_id: UUID,
    persona_id: str,
    activated_at: datetime,
    deactivated_at: datetime,
    conversation_excerpts: tuple[str, ...],
    pattern_matches: tuple[dict[str, Any], ...],
    reasoning_snapshot: dict[str, Any],
    activation_audit_trail: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "synthetic_persona": True,
        "content_marker": _CONTENT_MARKER,
        "tenant_id": str(tenant_id),
        "actor_id": str(actor_id),
        "persona_id": persona_id,
        "activated_at": activated_at.isoformat(),
        "deactivated_at": deactivated_at.isoformat(),
        "conversation_excerpts": list(conversation_excerpts),
        "pattern_matches": list(pattern_matches),
        "reasoning_snapshot": reasoning_snapshot,
        "activation_audit_trail": list(activation_audit_trail),
    }


def build_evidence_package(
    *,
    tenant_id: UUID,
    actor_id: UUID,
    persona_id: str,
    activated_at: datetime,
    deactivated_at: datetime,
    conversation_excerpts: tuple[str, ...],
    pattern_matches: tuple[dict[str, Any], ...],
    reasoning_snapshot: dict[str, Any],
    activation_audit_trail: tuple[str, ...],
) -> EvidencePackage:
    payload = _payload_dict(
        tenant_id=tenant_id,
        actor_id=actor_id,
        persona_id=persona_id,
        activated_at=activated_at,
        deactivated_at=deactivated_at,
        conversation_excerpts=conversation_excerpts,
        pattern_matches=pattern_matches,
        reasoning_snapshot=reasoning_snapshot,
        activation_audit_trail=activation_audit_trail,
    )
    json_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    content_hash = hashlib.sha256(json_payload.encode("utf-8")).hexdigest()
    return EvidencePackage(
        tenant_id=tenant_id,
        actor_id=actor_id,
        persona_id=persona_id,
        activated_at=activated_at,
        deactivated_at=deactivated_at,
        conversation_excerpts=conversation_excerpts,
        pattern_matches=pattern_matches,
        reasoning_snapshot=reasoning_snapshot,
        activation_audit_trail=activation_audit_trail,
        json_payload=json_payload,
        content_hash=content_hash,
    )
