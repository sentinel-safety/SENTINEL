# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import contextlib
import secrets
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.ingestion.app.main import create_app
from shared.auth.api_key import hash_api_key
from shared.config import Settings
from shared.schemas.enums import EventType

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio,
    pytest.mark.no_ingestion_auth_bypass,
]


async def _seed_tenant_and_key(
    admin_engine: AsyncEngine, *, revoked: bool = False, scope: str = "write"
) -> tuple[str, str, str]:
    tenant_id = str(uuid4())
    raw_secret = f"sk_{secrets.token_hex(4)}.{secrets.token_urlsafe(32)}"
    key_hash = hash_api_key(raw_secret)
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                "VALUES (:t, 'bug2', 'free', '{}', 30, '{}'::jsonb)"
            ),
            {"t": tenant_id},
        )
        revoked_at = "now()" if revoked else "NULL"
        await conn.execute(
            text(
                "INSERT INTO api_key (id, tenant_id, name, key_hash, key_prefix, "
                f"scope, revoked_at) VALUES (:id, :t, 'test', :h, :p, :s, {revoked_at})"
            ),
            {
                "id": str(uuid4()),
                "t": tenant_id,
                "h": key_hash,
                "p": raw_secret.split(".", 1)[0],
                "s": scope,
            },
        )
        actor_id = str(uuid4())
        await conn.execute(
            text(
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band) "
                "VALUES (:a, :t, :h, 'unknown')"
            ),
            {"a": actor_id, "t": tenant_id, "h": "a" * 64},
        )
    return tenant_id, raw_secret, actor_id


def _payload(tenant_id: str) -> dict[str, Any]:
    return {
        "idempotency_key": f"bug2-{uuid4()}",
        "tenant_id": tenant_id,
        "conversation_id": str(uuid4()),
        "actor_external_id_hash": "a" * 64,
        "target_actor_external_id_hashes": ["b" * 64],
        "event_type": EventType.MESSAGE.value,
        "timestamp": datetime.now(UTC).isoformat(),
        "content": "hi",
        "metadata": {},
    }


async def test_missing_authorization_returns_401(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id, _, _ = await _seed_tenant_and_key(admin_engine)
    app = create_app(Settings(env="test"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post("/v1/events", json=_payload(tenant_id))
    assert resp.status_code == 401
    assert resp.headers.get("www-authenticate", "").lower().startswith("bearer")


async def test_invalid_bearer_format_returns_401(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id, _, _ = await _seed_tenant_and_key(admin_engine)
    app = create_app(Settings(env="test"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/v1/events",
            json=_payload(tenant_id),
            headers={"Authorization": "Basic abc"},
        )
    assert resp.status_code == 401


async def test_wrong_secret_returns_401(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tenant_id, _, _ = await _seed_tenant_and_key(admin_engine)
    app = create_app(Settings(env="test"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/v1/events",
            json=_payload(tenant_id),
            headers={"Authorization": "Bearer sk_xyz.invalid"},
        )
    assert resp.status_code == 401


async def test_revoked_key_returns_401(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tenant_id, raw, _ = await _seed_tenant_and_key(admin_engine, revoked=True)
    app = create_app(Settings(env="test"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/v1/events",
            json=_payload(tenant_id),
            headers={"Authorization": f"Bearer {raw}"},
        )
    assert resp.status_code == 401


async def test_read_only_key_rejected(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tenant_id, raw, _ = await _seed_tenant_and_key(admin_engine, scope="read")
    app = create_app(Settings(env="test"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/v1/events",
            json=_payload(tenant_id),
            headers={"Authorization": f"Bearer {raw}"},
        )
    assert resp.status_code == 403


async def test_tenant_mismatch_returns_403(admin_engine: AsyncEngine, clean_tables: None) -> None:
    _, raw, _ = await _seed_tenant_and_key(admin_engine)
    other_tenant = str(uuid4())
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                "VALUES (:t, 'other', 'free', '{}', 30, '{}'::jsonb)"
            ),
            {"t": other_tenant},
        )
    app = create_app(Settings(env="test"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/v1/events",
            json=_payload(other_tenant),
            headers={"Authorization": f"Bearer {raw}"},
        )
    assert resp.status_code == 403


async def test_valid_key_reaches_downstream(admin_engine: AsyncEngine, clean_tables: None) -> None:
    """Valid key passes auth and the service attempts downstream calls (proves not-401/403)."""
    tenant_id, raw, _ = await _seed_tenant_and_key(admin_engine)
    settings = Settings(
        env="test",
        preprocess_base_url="http://preprocess",
        patterns_base_url="http://patterns",
        scoring_base_url="http://score",
        memory_base_url="http://memory",
        graph_base_url="http://graph",
        response_base_url="http://response",
    )
    app = create_app(settings)
    preprocess_called = False
    with respx.mock(assert_all_called=False) as router:
        preprocess_route = router.route(host="preprocess").mock(
            return_value=Response(500, text="downstream stub")
        )
        for host in ("patterns", "score", "memory", "graph", "response"):
            router.route(host=host).mock(return_value=Response(500, text="stub"))
        router.route(host="127.0.0.1", port=6333).pass_through()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
            with contextlib.suppress(Exception):
                await client.post(
                    "/v1/events",
                    json=_payload(tenant_id),
                    headers={"Authorization": f"Bearer {raw}"},
                )
        preprocess_called = preprocess_route.called
    assert preprocess_called, "auth layer blocked the request before reaching downstream"
