# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.gateway.app.main import create_app
from shared.config import Settings

pytestmark = pytest.mark.unit


def test_create_app_returns_fastapi_instance() -> None:
    app = create_app(Settings(env="test"))
    assert isinstance(app, FastAPI)


def test_create_app_sets_title_and_version() -> None:
    app = create_app(Settings(env="test"))
    assert app.title == "SENTINEL Gateway"
    assert app.version


def test_openapi_schema_available(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "SENTINEL Gateway"
