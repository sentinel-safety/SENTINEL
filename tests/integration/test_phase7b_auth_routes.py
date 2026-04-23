# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

from services.dashboard_bff.app.main import create_app
from shared.auth.jwt import issue_token
from shared.auth.keys import load_keypair
from tests.integration._phase7b_helpers import (
    auth_headers,
    fast_settings,
    seed_tenant,
    seed_user,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_login_happy_path(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    await seed_user(
        admin_engine,
        tid,
        email="alice@x.com",
        password="correct horse",  # pragma: allowlist secret
        role="admin",
    )
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/dashboard/api/auth/login",
            json={"email": "alice@x.com", "password": "correct horse"},  # pragma: allowlist secret
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"].count(".") == 2
    assert body["refresh_token"].count(".") == 2
    assert body["user"]["email"] == "alice@x.com"
    assert body["user"]["role"] == "admin"


async def test_login_rejects_bad_password(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    await seed_user(
        admin_engine,
        tid,
        email="bob@x.com",
        password="right",  # pragma: allowlist secret
        role="mod",
    )
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/dashboard/api/auth/login",
            json={"email": "bob@x.com", "password": "wrong"},  # pragma: allowlist secret
        )
    assert resp.status_code == 401


async def test_login_rejects_unknown_email(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/dashboard/api/auth/login",
            json={"email": "ghost@x.com", "password": "x"},
        )
    assert resp.status_code == 401


async def test_me_requires_bearer(admin_engine: AsyncEngine, clean_tables: None) -> None:
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get("/dashboard/api/auth/me")
    assert resp.status_code == 401


async def test_me_returns_user(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(
        admin_engine,
        tid,
        email="carol@x.com",
        password="pw",  # pragma: allowlist secret
        role="viewer",
    )
    settings = fast_settings()
    priv, _ = load_keypair(settings)
    now = datetime.now(UTC)
    token = issue_token(
        private_key_pem=priv,
        user_id=uid,
        tenant_id=uuid.UUID(tid),
        role="viewer",
        token_type="access",
        issued_at=now,
        expires_at=now + timedelta(minutes=15),
    )
    app = create_app(settings)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get("/dashboard/api/auth/me", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["email"] == "carol@x.com"


async def test_refresh_issues_new_access_token(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(
        admin_engine,
        tid,
        email="dan@x.com",
        password="pw",  # pragma: allowlist secret
        role="admin",
    )
    settings = fast_settings()
    priv, _ = load_keypair(settings)
    now = datetime.now(UTC)
    refresh = issue_token(
        private_key_pem=priv,
        user_id=uid,
        tenant_id=uuid.UUID(tid),
        role="admin",
        token_type="refresh",
        issued_at=now,
        expires_at=now + timedelta(days=14),
    )
    app = create_app(settings)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post("/dashboard/api/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert resp.json()["access_token"].count(".") == 2
