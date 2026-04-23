# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import uuid4

import pytest

from shared.errors import (
    ActorNotFoundError,
    InsufficientScopeError,
    InvalidApiKeyError,
    SentinelError,
    TenantNotFoundError,
    TenantQuotaExceededError,
)

pytestmark = pytest.mark.unit


def test_sentinel_error_to_payload_is_json_ready() -> None:
    e = SentinelError("boom", details={"reason": "kaboom"})
    payload = e.to_payload()
    assert payload == {
        "code": "sentinel.internal_error",
        "message": "boom",
        "details": {"reason": "kaboom"},
    }


def test_tenant_not_found_includes_id_in_payload() -> None:
    tid = uuid4()
    e = TenantNotFoundError(tid)
    assert e.http_status == 404
    assert e.to_payload()["details"] == {"tenant_id": str(tid)}


def test_actor_not_found_includes_ids() -> None:
    aid, tid = uuid4(), uuid4()
    e = ActorNotFoundError(aid, tid)
    assert e.to_payload()["details"] == {
        "actor_id": str(aid),
        "tenant_id": str(tid),
    }


def test_auth_errors_distinct_from_auth_base() -> None:
    assert InvalidApiKeyError.code != InsufficientScopeError.code
    assert InsufficientScopeError.http_status == 403
    assert InvalidApiKeyError.http_status == 401


def test_tenant_quota_is_rate_limited_code() -> None:
    e = TenantQuotaExceededError("over quota")
    assert e.http_status == 429
