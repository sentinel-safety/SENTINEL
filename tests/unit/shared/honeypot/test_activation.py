# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.honeypot.activation import ActivationDecision, evaluate_activation
from shared.schemas.enums import Jurisdiction

pytestmark = pytest.mark.unit

_US_ALLOWLIST: tuple[Jurisdiction, ...] = (Jurisdiction.US,)
_US_SCOPE: tuple[Jurisdiction, ...] = (Jurisdiction.US,)


def test_allows_when_every_gate_passes() -> None:
    d = evaluate_activation(
        actor_tier=4,
        tenant_feature_flags={"honeypot_enabled": True, "honeypot_legal_review_acknowledged": True},
        tenant_jurisdictions=(Jurisdiction.US,),
        jurisdiction_allowlist=_US_ALLOWLIST,
        persona_activation_scope=_US_SCOPE,
        tier_threshold=4,
    )
    assert d == ActivationDecision(allowed=True, reasons=())


def test_denies_when_tier_below_threshold() -> None:
    d = evaluate_activation(
        actor_tier=3,
        tenant_feature_flags={"honeypot_enabled": True, "honeypot_legal_review_acknowledged": True},
        tenant_jurisdictions=(Jurisdiction.US,),
        jurisdiction_allowlist=_US_ALLOWLIST,
        persona_activation_scope=_US_SCOPE,
        tier_threshold=4,
    )
    assert d.allowed is False
    assert "tier_below_threshold" in d.reasons


def test_denies_when_feature_flag_off() -> None:
    d = evaluate_activation(
        actor_tier=4,
        tenant_feature_flags={
            "honeypot_enabled": False,
            "honeypot_legal_review_acknowledged": True,
        },
        tenant_jurisdictions=(Jurisdiction.US,),
        jurisdiction_allowlist=_US_ALLOWLIST,
        persona_activation_scope=_US_SCOPE,
        tier_threshold=4,
    )
    assert d.allowed is False
    assert "feature_flag_disabled" in d.reasons


def test_denies_when_legal_review_not_acknowledged() -> None:
    d = evaluate_activation(
        actor_tier=4,
        tenant_feature_flags={
            "honeypot_enabled": True,
            "honeypot_legal_review_acknowledged": False,
        },
        tenant_jurisdictions=(Jurisdiction.US,),
        jurisdiction_allowlist=_US_ALLOWLIST,
        persona_activation_scope=_US_SCOPE,
        tier_threshold=4,
    )
    assert d.allowed is False
    assert "legal_review_not_acknowledged" in d.reasons


def test_denies_when_tenant_jurisdiction_outside_allowlist() -> None:
    d = evaluate_activation(
        actor_tier=4,
        tenant_feature_flags={"honeypot_enabled": True, "honeypot_legal_review_acknowledged": True},
        tenant_jurisdictions=(Jurisdiction.EU,),
        jurisdiction_allowlist=_US_ALLOWLIST,
        persona_activation_scope=_US_SCOPE,
        tier_threshold=4,
    )
    assert d.allowed is False
    assert "jurisdiction_not_in_allowlist" in d.reasons


def test_denies_when_persona_scope_does_not_overlap_tenant() -> None:
    d = evaluate_activation(
        actor_tier=4,
        tenant_feature_flags={"honeypot_enabled": True, "honeypot_legal_review_acknowledged": True},
        tenant_jurisdictions=(Jurisdiction.US,),
        jurisdiction_allowlist=_US_ALLOWLIST,
        persona_activation_scope=(Jurisdiction.UK,),
        tier_threshold=4,
    )
    assert d.allowed is False
    assert "persona_scope_mismatch" in d.reasons


def test_denies_when_allowlist_empty() -> None:
    d = evaluate_activation(
        actor_tier=4,
        tenant_feature_flags={"honeypot_enabled": True, "honeypot_legal_review_acknowledged": True},
        tenant_jurisdictions=(Jurisdiction.US,),
        jurisdiction_allowlist=(),
        persona_activation_scope=_US_SCOPE,
        tier_threshold=4,
    )
    assert d.allowed is False
    assert "jurisdiction_not_in_allowlist" in d.reasons


def test_reasons_are_cumulative_in_fixed_order() -> None:
    d = evaluate_activation(
        actor_tier=0,
        tenant_feature_flags={
            "honeypot_enabled": False,
            "honeypot_legal_review_acknowledged": False,
        },
        tenant_jurisdictions=(Jurisdiction.EU,),
        jurisdiction_allowlist=_US_ALLOWLIST,
        persona_activation_scope=(Jurisdiction.UK,),
        tier_threshold=4,
    )
    assert d.allowed is False
    assert d.reasons == (
        "tier_below_threshold",
        "feature_flag_disabled",
        "legal_review_not_acknowledged",
        "jurisdiction_not_in_allowlist",
        "persona_scope_mismatch",
    )
