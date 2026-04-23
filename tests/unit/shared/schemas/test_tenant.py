# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from shared.schemas import (
    ActionMode,
    ApiKey,
    ApiKeyScope,
    FeatureFlags,
    Jurisdiction,
    Tenant,
    TenantTier,
    WebhookEndpoint,
)

pytestmark = pytest.mark.unit


def _make_tenant(**overrides: object) -> Tenant:
    defaults = {
        "id": uuid4(),
        "name": "Acme Games",
        "created_at": datetime.now(UTC),
    }
    return Tenant.model_validate({**defaults, **overrides})


def test_tenant_has_sensible_defaults() -> None:
    t = _make_tenant()
    assert t.tier == TenantTier.FREE
    assert t.data_retention_days == 30
    assert t.compliance_jurisdictions == ()
    assert t.api_keys == ()
    assert t.webhook_endpoints == ()
    assert t.feature_flags.federation_enabled is False
    assert t.feature_flags.honeypot_enabled is False
    assert t.feature_flags.action_mode == ActionMode.ADVISORY


def test_tenant_rejects_naive_datetime() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        _make_tenant(created_at=datetime.now())  # noqa: DTZ005


def test_tenant_retention_days_bounded() -> None:
    with pytest.raises(ValidationError):
        _make_tenant(data_retention_days=0)
    with pytest.raises(ValidationError):
        _make_tenant(data_retention_days=3651)


def test_tenant_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError, match="Extra"):
        Tenant.model_validate(
            {
                "id": uuid4(),
                "name": "x",
                "created_at": datetime.now(UTC),
                "rogue_field": 1,
            }
        )


def test_tenant_is_frozen() -> None:
    t = _make_tenant()
    with pytest.raises(ValidationError):
        t.name = "changed"  # type: ignore[misc]


def test_active_api_keys_filters_revoked() -> None:
    tid = uuid4()
    now = datetime.now(UTC)
    active = ApiKey(
        id=uuid4(),
        tenant_id=tid,
        scope=ApiKeyScope.WRITE,
        hashed_value="a" * 64,
        created_at=now,
    )
    revoked = ApiKey(
        id=uuid4(),
        tenant_id=tid,
        scope=ApiKeyScope.READ,
        hashed_value="b" * 64,
        created_at=now,
        revoked_at=now,
    )
    t = _make_tenant(id=tid, api_keys=(active, revoked))
    assert t.active_api_keys() == (active,)


def test_feature_flags_roundtrip() -> None:
    f = FeatureFlags(
        federation_enabled=True,
        honeypot_enabled=True,
        action_mode=ActionMode.AUTO_ENFORCE,
        training_opt_in=True,
    )
    data = f.model_dump()
    assert FeatureFlags.model_validate(data) == f


def test_webhook_endpoint_requires_events() -> None:
    with pytest.raises(ValidationError):
        WebhookEndpoint(
            id=uuid4(),
            tenant_id=uuid4(),
            url="https://example.com/hook",
            events=(),
            secret_hash="c" * 64,
            created_at=datetime.now(UTC),
        )


def test_tenant_serialization_roundtrip() -> None:
    t = _make_tenant(
        compliance_jurisdictions=(Jurisdiction.EU, Jurisdiction.UK),
        tier=TenantTier.PRO,
    )
    data = t.model_dump(mode="json")
    restored = Tenant.model_validate(data)
    assert restored == t
