# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI, Header
from fastapi.testclient import TestClient

from shared.synthetic.access import authorized_researcher_check, require_researcher

pytestmark = pytest.mark.unit


def _make_app() -> FastAPI:
    app = FastAPI()

    async def _get_role(x_role: str = Header(default="viewer")) -> str:
        return x_role

    @app.get("/protected")
    async def _protected(role: str = Depends(require_researcher(_get_role))) -> dict[str, object]:
        return {"ok": True, "role": role}

    return app


_app = _make_app()
_client = TestClient(_app, raise_server_exceptions=False)


def test_researcher_role_allowed() -> None:
    assert authorized_researcher_check("researcher") is True
    resp = _client.get("/protected", headers={"x-role": "researcher"})
    assert resp.status_code == 200


def test_admin_role_allowed() -> None:
    assert authorized_researcher_check("admin") is True
    resp = _client.get("/protected", headers={"x-role": "admin"})
    assert resp.status_code == 200


def test_viewer_role_denied() -> None:
    assert authorized_researcher_check("viewer") is False
    resp = _client.get("/protected", headers={"x-role": "viewer"})
    assert resp.status_code == 403


def test_mod_role_denied() -> None:
    assert authorized_researcher_check("mod") is False
    resp = _client.get("/protected", headers={"x-role": "mod"})
    assert resp.status_code == 403


def test_auditor_role_denied() -> None:
    assert authorized_researcher_check("auditor") is False
    resp = _client.get("/protected", headers={"x-role": "auditor"})
    assert resp.status_code == 403
