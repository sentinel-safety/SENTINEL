# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid

import pytest

from services.dashboard_bff.app.schemas import (
    DashboardRole,
    LoginRequest,
    LoginResponse,
    SessionUser,
    UserResponse,
)

pytestmark = pytest.mark.unit


def test_session_user_is_frozen() -> None:
    u = SessionUser(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        email="a@x.com",
        role=DashboardRole.ADMIN,
        display_name="A",
    )
    with pytest.raises((TypeError, ValueError)):
        u.role = DashboardRole.VIEWER  # type: ignore[misc]


def test_login_request_rejects_empty_password() -> None:
    with pytest.raises(ValueError):
        LoginRequest(email="a@x.com", password="")


def test_login_response_shape() -> None:
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    resp = LoginResponse(
        access_token="a.b.c",
        refresh_token="d.e.f",
        user=UserResponse(
            id=uid,
            tenant_id=tid,
            email="a@x.com",
            role=DashboardRole.MOD,
            display_name="A",
        ),
    )
    assert resp.access_token == "a.b.c"
    assert resp.user.role == DashboardRole.MOD
