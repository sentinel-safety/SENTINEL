# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from services.classifier_first_pass.app.main import create_app
from shared.config import Settings

pytestmark = pytest.mark.unit


def _client() -> TestClient:
    return TestClient(create_app(Settings(env="test")), raise_server_exceptions=False)


def test_classify_returns_410() -> None:
    resp = _client().post("/internal/classify", json={})
    assert resp.status_code == 410
