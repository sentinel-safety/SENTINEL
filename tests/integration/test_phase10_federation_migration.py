# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_federation_tenant_secret_table_exists(admin_engine: AsyncEngine) -> None:
    async with admin_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='federation_tenant_secret'"
            )
        )
        cols = {r.column_name for r in result}
    assert {"tenant_id", "hmac_secret", "actor_pepper", "created_at"}.issubset(cols)


async def test_federation_publisher_table_exists(admin_engine: AsyncEngine) -> None:
    async with admin_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='federation_publisher'"
            )
        )
        cols = {r.column_name for r in result}
    assert {
        "tenant_id",
        "display_name",
        "jurisdictions",
        "reputation",
        "revoked_at",
        "created_at",
        "hmac_secret",
    }.issubset(cols)


async def test_federation_signal_table_exists(admin_engine: AsyncEngine) -> None:
    async with admin_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='federation_signal'"
            )
        )
        cols = {r.column_name for r in result}
    assert {
        "id",
        "publisher_tenant_id",
        "fingerprint",
        "signal_kinds",
        "flagged_at",
        "commit",
        "received_at",
    }.issubset(cols)


async def test_federation_reputation_event_table_exists(admin_engine: AsyncEngine) -> None:
    async with admin_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='federation_reputation_event'"
            )
        )
        cols = {r.column_name for r in result}
    assert {
        "id",
        "publisher_tenant_id",
        "reporter_tenant_id",
        "delta",
        "reason",
        "created_at",
    }.issubset(cols)


async def test_only_federation_tenant_secret_has_rls(admin_engine: AsyncEngine) -> None:
    async with admin_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT relname, relrowsecurity FROM pg_class "
                "WHERE relname IN ("
                "  'federation_tenant_secret',"
                "  'federation_publisher',"
                "  'federation_signal',"
                "  'federation_reputation_event'"
                ")"
            )
        )
        rows = {r.relname: r.relrowsecurity for r in result}
    assert rows.get("federation_tenant_secret") is True
    assert rows.get("federation_publisher") is False
    assert rows.get("federation_signal") is False
    assert rows.get("federation_reputation_event") is False
