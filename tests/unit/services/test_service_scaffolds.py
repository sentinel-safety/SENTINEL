# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import importlib
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from shared.config import Settings
from shared.observability import reset_observability
from tests._services import SERVICES

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _reset_observability() -> Iterator[None]:
    yield
    reset_observability()


@pytest.mark.parametrize(("module_path", "expected_service_name"), SERVICES)
def test_service_create_app_returns_fastapi(module_path: str, expected_service_name: str) -> None:
    module = importlib.import_module(module_path)
    app = module.create_app(Settings(env="test"))
    assert isinstance(app, FastAPI)
    assert app.state.settings.service_name == expected_service_name


@pytest.mark.parametrize(("module_path", "expected_service_name"), SERVICES)
def test_service_exposes_health_endpoint(module_path: str, expected_service_name: str) -> None:
    del expected_service_name
    module = importlib.import_module(module_path)
    app = module.create_app(Settings(env="test"))
    with TestClient(app) as client:
        assert client.get("/healthz").json() == {"status": "ok"}


@pytest.mark.parametrize(("module_path", "expected_service_name"), SERVICES)
def test_service_version_endpoint_reports_identity(
    module_path: str, expected_service_name: str
) -> None:
    module = importlib.import_module(module_path)
    app = module.create_app(Settings(env="test"))
    with TestClient(app) as client:
        payload = client.get("/version").json()
    assert payload["service"] == expected_service_name
    assert payload["environment"] == "test"
