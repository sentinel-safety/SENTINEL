# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


def test_healthz_returns_ok(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_returns_ready(client: TestClient) -> None:
    response = client.get("/readyz")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"


def test_version_endpoint_returns_service_metadata(client: TestClient) -> None:
    response = client.get("/version")
    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "sentinel-gateway"
    assert "version" in payload
    assert payload["environment"] == "test"
