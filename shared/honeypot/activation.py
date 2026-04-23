# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from pydantic import Field

from shared.schemas.base import FrozenModel
from shared.schemas.enums import Jurisdiction


class ActivationDecision(FrozenModel):
    allowed: bool
    reasons: tuple[str, ...] = Field(default=())


def evaluate_activation(
    *,
    actor_tier: int,
    tenant_feature_flags: dict[str, bool],
    tenant_jurisdictions: tuple[Jurisdiction, ...],
    jurisdiction_allowlist: tuple[Jurisdiction, ...],
    persona_activation_scope: tuple[Jurisdiction, ...],
    tier_threshold: int,
) -> ActivationDecision:
    reasons: list[str] = []
    if actor_tier < tier_threshold:
        reasons.append("tier_below_threshold")
    if not tenant_feature_flags.get("honeypot_enabled", False):
        reasons.append("feature_flag_disabled")
    if not tenant_feature_flags.get("honeypot_legal_review_acknowledged", False):
        reasons.append("legal_review_not_acknowledged")
    tenant_set = set(tenant_jurisdictions)
    if not tenant_set.intersection(jurisdiction_allowlist):
        reasons.append("jurisdiction_not_in_allowlist")
    if not tenant_set.intersection(persona_activation_scope):
        reasons.append("persona_scope_mismatch")
    return ActivationDecision(allowed=not reasons, reasons=tuple(reasons))
