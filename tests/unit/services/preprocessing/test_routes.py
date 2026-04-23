# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from services.preprocessing.app.main import create_app
from shared.config import Settings
from shared.schemas.enums import EventType

pytestmark = pytest.mark.unit


def _client() -> TestClient:
    return TestClient(create_app(Settings(env="test")))


def _body(content: str) -> dict[str, object]:
    return {
        "event": {
            "id": str(uuid4()),
            "tenant_id": str(uuid4()),
            "conversation_id": str(uuid4()),
            "actor_id": str(uuid4()),
            "target_actor_ids": [],
            "timestamp": datetime.now(UTC).isoformat(),
            "type": EventType.MESSAGE.value,
            "content_hash": "a" * 64,
        },
        "content": content,
        "recipient_age_bands": ["under_13"],
        "recipient_timezone": "UTC",
    }


def test_preprocess_route_returns_features() -> None:
    resp = _client().post("/internal/preprocess", json=_body("don't tell your parents"))
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["features"]["minor_recipient"] is True
    assert payload["features"]["normalized_content"] == "don't tell your parents"


def test_preprocess_rejects_malformed_body() -> None:
    resp = _client().post("/internal/preprocess", json={"event": {}, "content": "x"})
    assert resp.status_code == 422
