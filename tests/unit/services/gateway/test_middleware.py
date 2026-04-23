# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


def test_request_id_generated_when_absent(client: TestClient) -> None:
    response = client.get("/healthz")
    request_id = response.headers.get("x-request-id")
    assert request_id is not None
    UUID(request_id)


def test_request_id_propagated_when_provided(client: TestClient) -> None:
    provided = "01234567-89ab-cdef-0123-456789abcdef"
    response = client.get("/healthz", headers={"x-request-id": provided})
    assert response.headers["x-request-id"] == provided


def test_invalid_request_id_replaced(client: TestClient) -> None:
    response = client.get("/healthz", headers={"x-request-id": "not-a-uuid"})
    returned = response.headers["x-request-id"]
    UUID(returned)
    assert returned != "not-a-uuid"
