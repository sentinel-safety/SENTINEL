# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

import pytest

from shared.observability import (
    bind_actor_id,
    bind_request_id,
    bind_tenant_id,
    clear_context,
    current_context,
    log_context,
)

pytestmark = pytest.mark.unit

_TENANT = UUID("11111111-1111-1111-1111-111111111111")
_ACTOR = UUID("22222222-2222-2222-2222-222222222222")


def test_bind_tenant_id_adds_to_context() -> None:
    bind_tenant_id(_TENANT)
    assert current_context() == {"tenant_id": str(_TENANT)}


def test_bind_request_id_adds_to_context() -> None:
    bind_request_id("req-123")
    assert current_context()["request_id"] == "req-123"


def test_bind_actor_id_adds_to_context() -> None:
    bind_actor_id(_ACTOR)
    assert current_context()["actor_id"] == str(_ACTOR)


def test_clear_context_removes_all_bindings() -> None:
    bind_tenant_id(_TENANT)
    bind_request_id("req")
    clear_context()
    assert current_context() == {}


def test_log_context_scopes_bindings() -> None:
    bind_tenant_id(_TENANT)
    with log_context(job="score-decay"):
        assert current_context()["job"] == "score-decay"
        assert current_context()["tenant_id"] == str(_TENANT)
    assert "job" not in current_context()
    assert current_context()["tenant_id"] == str(_TENANT)


def _raise_inside_log_context() -> None:
    with log_context(step="risky"):
        assert current_context()["step"] == "risky"
        raise RuntimeError("boom")


def test_log_context_clears_on_exception() -> None:
    with pytest.raises(RuntimeError):
        _raise_inside_log_context()
    assert "step" not in current_context()
