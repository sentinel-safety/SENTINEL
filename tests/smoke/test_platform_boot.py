# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import importlib
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from shared.config import Settings
from tests._services import SERVICES

pytestmark = pytest.mark.smoke

REQUEST_ID_HEADER = "x-request-id"
META_PATHS = ("/healthz", "/readyz", "/version", "/openapi.json")


def _build(module_path: str) -> FastAPI:
    module = importlib.import_module(module_path)
    app = module.create_app(Settings(env="test"))
    assert isinstance(app, FastAPI)
    return app


@pytest.mark.parametrize(("module_path", "service_name"), SERVICES)
def test_every_service_boots_and_answers_meta_routes(module_path: str, service_name: str) -> None:
    app = _build(module_path)
    with TestClient(app) as client:
        for path in META_PATHS:
            response = client.get(path)
            assert response.status_code == 200, f"{service_name} {path} -> {response.status_code}"

        version_payload = client.get("/version").json()
        assert version_payload["service"] == service_name
        assert version_payload["environment"] == "test"

        health_payload = client.get("/healthz").json()
        assert health_payload == {"status": "ok"}

        ready_payload = client.get("/readyz").json()
        assert ready_payload == {"status": "ready"}


@pytest.mark.parametrize(("module_path", "service_name"), SERVICES)
def test_every_service_generates_request_id_when_absent(
    module_path: str, service_name: str
) -> None:
    del service_name
    app = _build(module_path)
    with TestClient(app) as client:
        response = client.get("/healthz")
    returned = response.headers.get(REQUEST_ID_HEADER)
    assert returned is not None
    UUID(returned)


@pytest.mark.parametrize(("module_path", "service_name"), SERVICES)
def test_every_service_echoes_valid_request_id(module_path: str, service_name: str) -> None:
    del service_name
    app = _build(module_path)
    provided = "11111111-2222-3333-4444-555555555555"
    with TestClient(app) as client:
        response = client.get("/healthz", headers={REQUEST_ID_HEADER: provided})
    assert response.headers[REQUEST_ID_HEADER] == provided


@pytest.mark.parametrize(("module_path", "service_name"), SERVICES)
def test_every_service_replaces_malformed_request_id(module_path: str, service_name: str) -> None:
    del service_name
    app = _build(module_path)
    with TestClient(app) as client:
        response = client.get("/healthz", headers={REQUEST_ID_HEADER: "not-a-uuid"})
    returned = response.headers[REQUEST_ID_HEADER]
    UUID(returned)
    assert returned != "not-a-uuid"


def test_service_catalog_lists_every_service_on_disk() -> None:
    import pathlib

    services_dir = pathlib.Path(__file__).resolve().parents[2] / "services"
    discovered = {
        entry.name
        for entry in services_dir.iterdir()
        if entry.is_dir() and not entry.name.startswith("_")
    }
    declared = {module_path.split(".")[1] for module_path, _ in SERVICES}
    assert discovered == declared, f"drift: on_disk={discovered} declared={declared}"
