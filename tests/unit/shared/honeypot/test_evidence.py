# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from shared.honeypot.evidence import EvidencePackage, build_evidence_package

pytestmark = pytest.mark.unit


def _ts() -> datetime:
    return datetime(2026, 4, 20, 12, 0, tzinfo=UTC)


def _base_pkg(
    *,
    tenant_id: UUID,
    actor_id: UUID,
    conversation_excerpts: tuple[str, ...] = (),
) -> EvidencePackage:
    return build_evidence_package(
        tenant_id=tenant_id,
        actor_id=actor_id,
        persona_id="emma-13-us-east",
        conversation_excerpts=conversation_excerpts,
        pattern_matches=({"pattern_name": "secrecy_request", "confidence": 0.82},),
        reasoning_snapshot={"new_tier": "restrict", "new_score": 72},
        activation_audit_trail=("a",),
        activated_at=_ts(),
        deactivated_at=_ts(),
    )


def test_build_evidence_package_contains_synthetic_marker() -> None:
    pkg = _base_pkg(tenant_id=uuid4(), actor_id=uuid4(), conversation_excerpts=("actor: hi",))
    assert pkg.synthetic_persona is True
    assert "SYNTHETIC" in pkg.content_marker


def test_content_hash_is_stable_for_same_input() -> None:
    tid = UUID("11111111-1111-1111-1111-111111111111")
    aid = UUID("22222222-2222-2222-2222-222222222222")
    a = _base_pkg(tenant_id=tid, actor_id=aid, conversation_excerpts=("actor: hi",))
    b = _base_pkg(tenant_id=tid, actor_id=aid, conversation_excerpts=("actor: hi",))
    assert a.content_hash == b.content_hash
    assert len(a.content_hash) == 64


def test_content_hash_changes_if_excerpts_change() -> None:
    tid = UUID("11111111-1111-1111-1111-111111111111")
    aid = UUID("22222222-2222-2222-2222-222222222222")
    a = _base_pkg(tenant_id=tid, actor_id=aid, conversation_excerpts=("x",))
    b = _base_pkg(tenant_id=tid, actor_id=aid, conversation_excerpts=("x", "y"))
    assert a.content_hash != b.content_hash


def test_evidence_package_is_frozen() -> None:
    pkg = _base_pkg(tenant_id=uuid4(), actor_id=uuid4())
    with pytest.raises(ValidationError):
        pkg.actor_id = uuid4()  # type: ignore[misc]


def test_evidence_package_json_payload_sorted() -> None:
    pkg = build_evidence_package(
        tenant_id=UUID("11111111-1111-1111-1111-111111111111"),
        actor_id=UUID("22222222-2222-2222-2222-222222222222"),
        persona_id="emma-13-us-east",
        conversation_excerpts=("a", "b"),
        pattern_matches=({"pattern_name": "secrecy_request"},),
        reasoning_snapshot={"z": 1, "a": 2},
        activation_audit_trail=("a",),
        activated_at=_ts(),
        deactivated_at=_ts(),
    )
    assert pkg.json_payload.startswith("{")
    assert '"synthetic_persona":true' in pkg.json_payload
