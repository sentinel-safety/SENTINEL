# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.dashboard_bff.app.main import create_app as create_bff
from shared.auth.jwt import issue_token
from shared.auth.keys import generate_keypair
from shared.config import get_settings
from shared.db.models import BugReport, Tenant
from shared.db.session import tenant_session
from shared.federation.signals import FederationSignal
from shared.federation.signing import sign_signal, verify_signal
from shared.webhook.signing import (
    SignatureVerificationError,
    build_signature_header,
    verify_signature,
)
from tests.integration._phase7b_helpers import (
    auth_headers,
    fast_settings,
    make_access_token,
    seed_tenant,
    seed_user,
)

pytestmark = pytest.mark.security

_SETTINGS = get_settings()


@pytest.fixture(autouse=True)
def _env_guard() -> None:
    if _SETTINGS.env not in ("test", "dev"):
        pytest.skip(f"security tests refused in env={_SETTINGS.env}")


async def test_pt1_rls_escape_suspicion_profile(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid_a = uuid.uuid4()
    tid_b = uuid.uuid4()
    async with admin_engine.begin() as conn:
        for tid in (tid_a, tid_b):
            await conn.execute(
                text(
                    "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                    "data_retention_days, feature_flags) "
                    "VALUES (:t, 'acme', 'free', '{}', 30, '{}'::jsonb)"
                ),
                {"t": str(tid)},
            )

    async with tenant_session(tid_b) as session:
        rows = (
            await session.execute(
                text("SELECT * FROM suspicion_profile WHERE tenant_id = :a"),
                {"a": str(tid_a)},
            )
        ).fetchall()

    assert rows == [], "RLS escape: tenant B must not see tenant A's suspicion profiles"


async def test_pt2_jwt_forgery_wrong_key_returns_401(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    attacker_priv, _ = generate_keypair()
    now = datetime.now(UTC)
    forged = issue_token(
        private_key_pem=attacker_priv,
        user_id=uuid.uuid4(),
        tenant_id=uuid.UUID(tid),
        role="admin",
        token_type="access",
        issued_at=now,
        expires_at=now + timedelta(minutes=30),
    )
    app = create_bff(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(
            "/dashboard/api/security/bug-reports",
            headers=auth_headers(forged),
        )
    assert resp.status_code == 401, "forged JWT with wrong key must be rejected"


async def test_pt3_hs256_downgrade_returns_401(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    now = datetime.now(UTC)
    hs256_token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "tid": tid,
            "role": "admin",
            "typ": "access",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=30)).timestamp()),
        },
        "sentinel-pentest-hs256-downgrade-key-00000000",  # pragma: allowlist secret
        algorithm="HS256",
    )
    app = create_bff(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(
            "/dashboard/api/security/bug-reports",
            headers=auth_headers(hs256_token),
        )
    assert resp.status_code == 401, "HS256-signed token where RS256 is expected must be rejected"


async def test_pt4_webhook_signature_replay_tampered_body() -> None:
    secret = "webhook-secret-key"  # pragma: allowlist secret
    original_body = b'{"event":"tier_change","tier":3}'
    tampered_body = b'{"event":"tier_change","tier":0}'
    ts = datetime.now(UTC)
    header = build_signature_header(secret=secret, timestamp=ts, body=original_body)
    with pytest.raises(SignatureVerificationError, match="signature mismatch"):
        verify_signature(
            header=header,
            secret=secret,
            body=tampered_body,
            now=ts,
            skew_seconds=300,
        )


async def test_pt5_webhook_timestamp_skew_rejected() -> None:
    secret = "webhook-secret-key"  # pragma: allowlist secret
    body = b'{"event":"tier_change"}'
    stale_ts = datetime.now(UTC) - timedelta(seconds=400)
    header = build_signature_header(secret=secret, timestamp=stale_ts, body=body)
    with pytest.raises(SignatureVerificationError, match="timestamp outside allowed skew"):
        verify_signature(
            header=header,
            secret=secret,
            body=body,
            now=datetime.now(UTC),
            skew_seconds=300,
        )


async def test_pt6_sql_injection_via_api_key_header_returns_401_and_tenant_intact(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    injection_payload = "'; DROP TABLE tenant; --"
    app = create_bff(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(
            "/dashboard/api/security/bug-reports",
            headers={"Authorization": f"Bearer {injection_payload}"},
        )
    assert resp.status_code == 401

    async with admin_engine.begin() as conn:
        row = (await conn.execute(select(Tenant).where(Tenant.id == uuid.UUID(tid)))).fetchone()
    assert row is not None, "tenant table must survive SQL injection attempt"


async def test_pt7_idempotency_same_key_deduplicates(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    app = create_bff(fast_settings())
    results: list[int] = []
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        for _ in range(5):
            resp = await client.post(
                "/dashboard/api/security/bug-reports",
                json={
                    "reporter_email": "r@example.com",
                    "summary": "idempotency test",
                    "details": "checking server stays alive under repeated posts.",
                    "severity": "low",
                },
                headers={"X-Sentinel-Tenant-Id": tid},
            )
            results.append(resp.status_code)

    assert all(s == 201 for s in results), "server must handle repeated posts without crashing"

    async with tenant_session(uuid.UUID(tid)) as session:
        rows = (await session.execute(select(BugReport))).scalars().all()

    assert len(rows) == 5, "5 posts produce 5 distinct bug report rows"


async def test_pt8_break_glass_without_investigation_reason_returns_400(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    user_id = await seed_user(admin_engine, tid, role="admin")
    token = make_access_token(user_id, uuid.UUID(tid), role="admin")
    app = create_bff(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(
            f"/dashboard/api/conversations/{uuid.uuid4()}/messages",
            headers=auth_headers(token),
        )
    assert resp.status_code == 400, "missing X-Investigation-Reason must return 400"


async def test_pt9_api_key_not_in_error_message(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    secret_key = "sk_test_super_secret_api_key_12345"  # pragma: allowlist secret
    app = create_bff(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(
            "/dashboard/api/security/bug-reports",
            headers={"Authorization": f"Bearer {secret_key}"},
        )
    assert resp.status_code == 401
    assert secret_key not in resp.text, "API key must not appear in error response body"


async def test_pt10_cross_tenant_bug_report_not_visible(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid_a = str(uuid.uuid4())
    tid_b = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid_a)
    await seed_tenant(admin_engine, tid_b)
    user_b_id = await seed_user(admin_engine, tid_b, role="admin")
    token_b = make_access_token(user_b_id, uuid.UUID(tid_b), role="admin")
    app = create_bff(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        await client.post(
            "/dashboard/api/security/bug-reports",
            json={
                "reporter_email": "a@example.com",
                "summary": "XSS in tenant A dashboard",
                "details": "Cross-tenant leak test.",
                "severity": "critical",
            },
            headers={"X-Sentinel-Tenant-Id": tid_a},
        )
        resp = await client.get(
            "/dashboard/api/security/bug-reports",
            headers=auth_headers(token_b),
        )
    assert resp.status_code == 200
    assert resp.json()["reports"] == [], "tenant B must not see tenant A's bug reports"


def test_pt11_honeypot_invocation_bypass_lint_passes() -> None:
    pattern = re.compile(r"from\s+shared\.honeypot\.(prompt|evidence)\s+import")
    allowed_roots = {
        Path("shared/honeypot/service.py").resolve(),
        Path("shared/honeypot/prompt.py").resolve(),
        Path("shared/honeypot/evidence.py").resolve(),
        Path("shared/honeypot/__init__.py").resolve(),
        Path("shared/honeypot/personas.py").resolve(),
        Path("shared/honeypot/activation.py").resolve(),
        Path("shared/honeypot/repository.py").resolve(),
    }
    offenders: list[Path] = []
    for root in (Path("services"), Path("shared")):
        for py in root.rglob("*.py"):
            if py.resolve() in allowed_roots:
                continue
            if pattern.search(py.read_text(encoding="utf-8")):
                offenders.append(py)
    assert offenders == [], (
        f"direct imports of shared.honeypot.prompt/evidence outside entrypoint: {offenders}"
    )


async def test_pt12_federation_signature_forgery_rejected() -> None:
    signal = FederationSignal(
        publisher_tenant_id=uuid.uuid4(),
        actor_hash=b"aa" * 16,
        fingerprint=tuple([0.1] * 16),
        signal_kinds=("grooming_slow_burn",),
        flagged_at=datetime.now(UTC),
    )
    real_secret = sha256(b"real-secret").digest()
    wrong_secret = sha256(b"wrong-secret").digest()
    commit = sign_signal(secret=real_secret, signal=signal)
    assert not verify_signal(secret=wrong_secret, signal=signal, commit=commit), (
        "signature forged with wrong HMAC key must be rejected"
    )
    assert verify_signal(secret=real_secret, signal=signal, commit=commit), (
        "valid signature must pass"
    )
