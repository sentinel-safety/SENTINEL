# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.dashboard_bff.app.user_repository import create_user
from shared.auth.jwt import Role, issue_token
from shared.auth.keys import generate_keypair, load_keypair
from shared.auth.passwords import build_hasher, hash_password
from shared.config import Settings
from shared.db.session import tenant_session

_FAST_PRIV, _FAST_PUB = generate_keypair()


def fast_settings() -> Settings:
    return Settings(
        env="dev",
        dashboard_jwt_private_key_pem=_FAST_PRIV,
        dashboard_jwt_public_key_pem=_FAST_PUB,
        dashboard_argon2_time_cost=1,
        dashboard_argon2_memory_cost=8,
        dashboard_argon2_parallelism=1,
    )


async def seed_tenant(admin_engine: AsyncEngine, tid: str) -> None:
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                "VALUES (:t, 'acme', 'free', '{}', 30, '{}'::jsonb)"
            ),
            {"t": tid},
        )


async def seed_actor(
    admin_engine: AsyncEngine,
    tenant_id: str,
    actor_id: str,
    age_band: str = "unknown",
) -> None:
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band) "
                "VALUES (:a, :t, :h, :b)"
            ),
            {
                "a": actor_id,
                "t": tenant_id,
                "h": uuid.uuid4().hex + "0" * 32,
                "b": age_band,
            },
        )


async def seed_suspicion_profile(
    admin_engine: AsyncEngine,
    tenant_id: str,
    actor_id: str,
    *,
    tier: int,
    score: int,
) -> None:
    now = datetime.now(UTC)
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO suspicion_profile "
                "(tenant_id, actor_id, current_score, tier, tier_entered_at, "
                "last_updated, last_decay_applied) "
                "VALUES (:t, :a, :s, :tier, :now, :now, :now)"
            ),
            {
                "t": tenant_id,
                "a": actor_id,
                "s": score,
                "tier": tier,
                "now": now,
            },
        )


async def seed_user(
    admin_engine: AsyncEngine,
    tenant_id: str,
    *,
    email: str | None = None,
    password: str = "pw",
    role: str = "admin",
) -> uuid.UUID:
    fast = build_hasher(time_cost=1, memory_cost=8, parallelism=1)
    digest = hash_password(password, hasher=fast)
    resolved_email = email or f"{uuid.uuid4().hex[:8]}@x.com"
    async with tenant_session(uuid.UUID(tenant_id)) as session:
        user = await create_user(
            session,
            tenant_id=uuid.UUID(tenant_id),
            email=resolved_email,
            password_hash=digest,
            role=role,
            display_name=resolved_email,
        )
    return user.id


def make_access_token(
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    role: Role = "admin",
    ttl_minutes: int = 30,
) -> str:
    priv, _ = load_keypair(fast_settings())
    now = datetime.now(UTC)
    return issue_token(
        private_key_pem=priv,
        user_id=user_id,
        tenant_id=tenant_id,
        role=role,
        token_type="access",
        issued_at=now,
        expires_at=now + timedelta(minutes=ttl_minutes),
    )


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def issue_admin_token(*, tenant_id: uuid.UUID, settings: Settings) -> str:
    priv, _ = load_keypair(settings)
    now = datetime.now(UTC)
    return issue_token(
        private_key_pem=priv,
        user_id=uuid.uuid4(),
        tenant_id=tenant_id,
        role="admin",
        token_type="access",
        issued_at=now,
        expires_at=now + timedelta(minutes=30),
    )
