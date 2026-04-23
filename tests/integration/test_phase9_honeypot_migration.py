# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_activation_log_table_exists(admin_engine: AsyncEngine) -> None:
    async with admin_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='honeypot_activation_log'"
            )
        )
        cols = {r.column_name for r in result}
    assert {
        "id",
        "tenant_id",
        "actor_id",
        "persona_id",
        "activated_at",
        "deactivated_at",
        "decision",
        "decision_reasons",
        "evidence_package_id",
    }.issubset(cols)


async def test_evidence_package_table_exists(admin_engine: AsyncEngine) -> None:
    async with admin_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='honeypot_evidence_package'"
            )
        )
        cols = {r.column_name for r in result}
    assert {"id", "tenant_id", "actor_id", "content_hash", "json_payload", "created_at"}.issubset(
        cols
    )


async def test_both_tables_have_rls_enabled(admin_engine: AsyncEngine) -> None:
    async with admin_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class "
                "WHERE relname IN ('honeypot_activation_log','honeypot_evidence_package')"
            )
        )
        rows = {r.relname: (r.relrowsecurity, r.relforcerowsecurity) for r in result}
    for name in ("honeypot_activation_log", "honeypot_evidence_package"):
        assert rows[name] == (True, True)


async def test_activation_log_decision_constraint(admin_engine: AsyncEngine) -> None:
    async with admin_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT conname FROM pg_constraint "
                "WHERE conrelid='honeypot_activation_log'::regclass AND contype='c'"
            )
        )
        names = {r.conname for r in result}
    assert "ck_honeypot_decision_valid" in names


async def test_evidence_package_content_hash_len_constraint(admin_engine: AsyncEngine) -> None:
    async with admin_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT conname FROM pg_constraint "
                "WHERE conrelid='honeypot_evidence_package'::regclass AND contype='c'"
            )
        )
        names = {r.conname for r in result}
    assert "ck_honeypot_content_hash_len" in names
