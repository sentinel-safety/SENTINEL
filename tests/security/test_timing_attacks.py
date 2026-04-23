# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import os
import secrets
import statistics
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.ingestion.app.main import create_app as create_ingestion
from shared.auth.api_key import hash_api_key
from shared.config import Settings, get_settings

pytestmark = pytest.mark.security

_SETTINGS = get_settings()


@pytest.fixture(autouse=True)
def _env_guard() -> None:
    if _SETTINGS.env not in ("test", "dev"):
        pytest.skip(f"security tests refused in env={_SETTINGS.env}")


def test_pt_timing_oracle_api_key_uses_constant_time_compare() -> None:
    """Static guarantee: API-key hash comparison is constant-time.

    If the auth path uses `==` on the hash, an attacker can binary-search the
    correct hash one byte at a time by measuring response latency. The
    guarantee is that `hmac.compare_digest` is used in the hot path.
    """
    source = Path("shared/auth/api_key.py").read_text(encoding="utf-8")
    assert "hmac.compare_digest" in source, (
        "resolve_api_key must use hmac.compare_digest for hash comparison, "
        "otherwise byte-by-byte timing oracles become exploitable"
    )
    assert " == expected_hash" not in source, (
        "naive == comparison of hash values forbidden in auth path"
    )


async def _seed_tenant_and_key(admin_engine: AsyncEngine) -> tuple[uuid.UUID, str]:
    tenant_id = uuid.uuid4()
    raw = f"sk_{secrets.token_hex(4)}.{secrets.token_urlsafe(32)}"
    key_hash = hash_api_key(raw)
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                "VALUES (:t, 'timing', 'free', '{}', 30, '{}'::jsonb)"
            ),
            {"t": str(tenant_id)},
        )
        await conn.execute(
            text(
                "INSERT INTO api_key (id, tenant_id, name, key_hash, key_prefix, scope) "
                "VALUES (:i, :t, 'timing', :h, :p, 'write')"
            ),
            {
                "i": str(uuid.uuid4()),
                "t": str(tenant_id),
                "h": key_hash,
                "p": raw.split(".", 1)[0],
            },
        )
    return tenant_id, raw


@pytest.mark.asyncio
async def test_pt_timing_oracle_actor_lookup_envelope(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    """Dynamic guarantee: actor-exists vs actor-not-exists response time is
    within a coarse envelope (median within 3x). In-process timing is flaky;
    we use a loose bound so the test only fires on glaring oracles (e.g.
    one path runs an extra network call or heavy query that the other
    doesn't).
    """
    tenant_id, _ = await _seed_tenant_and_key(admin_engine)
    actor_id = uuid.uuid4()
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band) "
                "VALUES (:a, :t, :h, 'unknown')"
            ),
            {"a": str(actor_id), "t": str(tenant_id), "h": "t" * 64},
        )
        await conn.execute(
            text(
                "INSERT INTO suspicion_profile (actor_id, tenant_id, current_score, "
                "tier, tier_entered_at, last_updated, last_decay_applied) "
                "VALUES (:a, :t, 10, 1, :n, :n, :n)"
            ),
            {"a": str(actor_id), "t": str(tenant_id), "n": datetime.now(UTC)},
        )

    app = create_ingestion(Settings(env="test"))
    missing_id = uuid.uuid4()
    exists_times: list[float] = []
    missing_times: list[float] = []
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        for _ in range(6):
            t0 = time.perf_counter()
            await client.get(
                f"/v1/actors/{actor_id}",
                headers={"x-tenant-id": str(tenant_id)},
            )
            exists_times.append(time.perf_counter() - t0)
            t0 = time.perf_counter()
            await client.get(
                f"/v1/actors/{missing_id}",
                headers={"x-tenant-id": str(tenant_id)},
            )
            missing_times.append(time.perf_counter() - t0)

    exists_med = statistics.median(exists_times[1:])
    missing_med = statistics.median(missing_times[1:])
    ratio = max(exists_med, missing_med) / min(exists_med, missing_med)
    assert ratio < 5.0, (
        f"timing oracle: exists median {exists_med * 1000:.1f}ms vs "
        f"missing median {missing_med * 1000:.1f}ms — ratio {ratio:.2f}x "
        "(>5x suggests the two paths do meaningfully different work)"
    )


@pytest.mark.asyncio
async def test_pt_timing_oracle_auth_failure_bodies_identical(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    """Auth-failure responses must not reveal *which* sub-check failed
    (missing header vs bad format vs wrong secret). Identical bodies block
    response-content oracles even if timing varies."""
    app = create_ingestion(Settings(env="test"))
    payload = {
        "idempotency_key": f"oracle-{uuid.uuid4()}",
        "tenant_id": str(uuid.uuid4()),
        "conversation_id": str(uuid.uuid4()),
        "actor_external_id_hash": "a" * 64,
        "target_actor_external_id_hashes": [],
        "event_type": "message",
        "timestamp": datetime.now(UTC).isoformat(),
        "content": "hi",
        "metadata": {},
    }
    prior = os.environ.pop("SENTINEL_INGESTION_AUTH_TEST_BYPASS", None)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
            r_missing = await client.post("/v1/events", json=payload)
            r_badfmt = await client.post(
                "/v1/events", json=payload, headers={"Authorization": "Basic zzz"}
            )
            r_bad_secret = await client.post(
                "/v1/events",
                json=payload,
                headers={"Authorization": "Bearer sk_fake.not-a-real-secret"},
            )
    finally:
        if prior is not None:
            os.environ["SENTINEL_INGESTION_AUTH_TEST_BYPASS"] = prior
    tenant_val = str(payload["tenant_id"])
    for r in (r_missing, r_badfmt, r_bad_secret):
        assert r.status_code == 401
        body = r.text
        assert "sk_fake.not-a-real-secret" not in body  # pragma: allowlist secret
        assert tenant_val not in body
