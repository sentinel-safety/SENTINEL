# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException

from services.dashboard_bff.app.dependencies import require_roles
from services.dashboard_bff.app.schemas import DashboardRole, SessionUser

pytestmark = pytest.mark.unit


def _user(role: DashboardRole) -> SessionUser:
    return SessionUser(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        email="a@x.com",
        role=role,
        display_name="A",
    )


def test_require_roles_allows_matching_role() -> None:
    dep = require_roles(DashboardRole.ADMIN, DashboardRole.MOD)
    got = dep(current_user=_user(DashboardRole.ADMIN))
    assert got.role == DashboardRole.ADMIN


def test_require_roles_denies_mismatched_role() -> None:
    dep = require_roles(DashboardRole.ADMIN)
    with pytest.raises(HTTPException) as exc_info:
        dep(current_user=_user(DashboardRole.VIEWER))
    assert exc_info.value.status_code == 403
