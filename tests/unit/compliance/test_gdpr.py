# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from compliance.gdpr import (
    ErasureRequest,
    ErasureRequestStatus,
    LawfulBasis,
    LawfulBasisDeclaration,
)

pytestmark = pytest.mark.unit

_TENANT = UUID("11111111-1111-1111-1111-111111111111")
_ACTOR = UUID("22222222-2222-2222-2222-222222222222")
_REQ = UUID("33333333-3333-3333-3333-333333333333")
_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


def test_lawful_basis_declaration_roundtrips() -> None:
    decl = LawfulBasisDeclaration(
        tenant_id=_TENANT,
        basis=LawfulBasis.LEGITIMATE_INTERESTS,
        documented_at=_NOW,
        documentation_uri="https://example.com/lawful-basis",
    )
    assert decl.basis is LawfulBasis.LEGITIMATE_INTERESTS
    assert decl.tenant_id == _TENANT


def test_erasure_request_terminal_states() -> None:
    completed = ErasureRequest(
        request_id=_REQ,
        tenant_id=_TENANT,
        actor_id=_ACTOR,
        received_at=_NOW,
        status=ErasureRequestStatus.COMPLETED,
        completed_at=_NOW,
    )
    rejected = completed.model_copy(update={"status": ErasureRequestStatus.REJECTED})
    in_progress = completed.model_copy(update={"status": ErasureRequestStatus.IN_PROGRESS})
    assert completed.is_terminal()
    assert rejected.is_terminal()
    assert not in_progress.is_terminal()
