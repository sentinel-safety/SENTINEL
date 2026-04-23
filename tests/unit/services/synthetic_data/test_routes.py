# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from services.dashboard_bff.app.schemas import DashboardRole, SessionUser
from services.synthetic_data.app.dependencies import get_current_user
from services.synthetic_data.app.main import create_app
from shared.config import Settings
from shared.synthetic.axes import GroomingStage

pytestmark = pytest.mark.unit

_AXES = {
    "demographics": [{"age_band": "14-15", "gender": "male", "regional_context": "UK"}],
    "platforms": ["dm"],
    "communication_styles": ["casual_typing"],
    "languages": ["en"],
}
_STAGE_MIX = {"weights": {stage.value: 1 for stage in GroomingStage}}


def _make_user(role: DashboardRole) -> SessionUser:
    return SessionUser(
        id=uuid4(),
        tenant_id=uuid4(),
        email="user@test.com",
        role=role,
        display_name="Test",
    )


def _app_with_user(user: SessionUser) -> TestClient:
    app = create_app(Settings(env="test"))
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def test_generate_requires_auth_returns_401_without_token() -> None:
    app = create_app(Settings(env="test"))
    client = TestClient(app)
    resp = client.post(
        "/internal/synthetic/generate",
        json={"axes": _AXES, "stage_mix": _STAGE_MIX, "count": 2, "seed": 42},
    )
    assert resp.status_code == 401


def test_generate_rejects_viewer_with_403() -> None:
    client = _app_with_user(_make_user(DashboardRole.VIEWER))
    resp = client.post(
        "/internal/synthetic/generate",
        json={"axes": _AXES, "stage_mix": _STAGE_MIX, "count": 2, "seed": 42},
    )
    assert resp.status_code == 403


def test_fetch_dataset_rejects_viewer_with_403() -> None:
    client = _app_with_user(_make_user(DashboardRole.VIEWER))
    resp = client.get(f"/internal/synthetic/datasets/{uuid4()}")
    assert resp.status_code == 403


def test_fetch_dataset_rejects_mod_with_403() -> None:
    client = _app_with_user(_make_user(DashboardRole.MOD))
    resp = client.get(f"/internal/synthetic/datasets/{uuid4()}")
    assert resp.status_code == 403
