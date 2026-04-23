# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from shared.audit import GENESIS_HASH, HASH_HEX_LEN, append_entry, verify_chain
from shared.db import AuditLogEntry, Tenant, tenant_session
from shared.errors.exceptions import AuditChainBrokenError, AuditTamperedError

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed_tenant(admin_engine: AsyncEngine, name: str = "audit") -> UUID:
    factory = async_sessionmaker(bind=admin_engine, expire_on_commit=False, autoflush=False)
    async with factory() as s, s.begin():
        t = Tenant(name=name, tier="free")
        s.add(t)
        await s.flush()
        return t.id


async def test_first_entry_links_to_genesis_hash(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    tid = await _seed_tenant(admin_engine)
    async with tenant_session(tid) as s:
        entry = await append_entry(
            s, tenant_id=tid, event_type="tenant.created", details={"by": "system"}
        )
    assert entry.sequence == 1
    assert entry.previous_entry_hash == GENESIS_HASH
    assert len(entry.entry_hash) == HASH_HEX_LEN


async def test_subsequent_entry_links_to_prior_entry_hash(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    tid = await _seed_tenant(admin_engine)
    async with tenant_session(tid) as s:
        first = await append_entry(s, tenant_id=tid, event_type="a")
        second = await append_entry(s, tenant_id=tid, event_type="b")
    assert second.sequence == 2
    assert second.previous_entry_hash == first.entry_hash


async def test_verify_passes_for_intact_chain(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    tid = await _seed_tenant(admin_engine)
    async with tenant_session(tid) as s:
        for i in range(5):
            await append_entry(s, tenant_id=tid, event_type=f"t.{i}", details={"i": i})
    async with tenant_session(tid) as s:
        assert await verify_chain(s, tid) == 5


async def test_verify_returns_zero_for_empty_tenant(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    tid = await _seed_tenant(admin_engine)
    async with tenant_session(tid) as s:
        assert await verify_chain(s, tid) == 0


async def test_tamper_with_details_raises_tampered(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    tid = await _seed_tenant(admin_engine)
    async with tenant_session(tid) as s:
        await append_entry(s, tenant_id=tid, event_type="a", details={"k": 1})
    factory = async_sessionmaker(bind=admin_engine, expire_on_commit=False, autoflush=False)
    async with factory() as s, s.begin():
        await s.execute(
            update(AuditLogEntry).where(AuditLogEntry.tenant_id == tid).values(details={"k": 2})
        )
    async with tenant_session(tid) as s:
        with pytest.raises(AuditTamperedError):
            await verify_chain(s, tid)


async def test_tamper_with_entry_hash_raises_tampered(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    tid = await _seed_tenant(admin_engine)
    async with tenant_session(tid) as s:
        await append_entry(s, tenant_id=tid, event_type="a")
    factory = async_sessionmaker(bind=admin_engine, expire_on_commit=False, autoflush=False)
    async with factory() as s, s.begin():
        await s.execute(
            update(AuditLogEntry)
            .where(AuditLogEntry.tenant_id == tid)
            .values(entry_hash="f" * HASH_HEX_LEN)
        )
    async with tenant_session(tid) as s:
        with pytest.raises(AuditTamperedError):
            await verify_chain(s, tid)


async def test_broken_previous_hash_link_raises_chain_broken(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    tid = await _seed_tenant(admin_engine)
    async with tenant_session(tid) as s:
        await append_entry(s, tenant_id=tid, event_type="a")
        await append_entry(s, tenant_id=tid, event_type="b")
    factory = async_sessionmaker(bind=admin_engine, expire_on_commit=False, autoflush=False)
    async with factory() as s, s.begin():
        await s.execute(
            update(AuditLogEntry)
            .where(
                AuditLogEntry.tenant_id == tid,
                AuditLogEntry.sequence == 2,
            )
            .values(previous_entry_hash="9" * HASH_HEX_LEN)
        )
    async with tenant_session(tid) as s:
        with pytest.raises(AuditChainBrokenError):
            await verify_chain(s, tid)


async def test_sequence_gap_raises_chain_broken(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    tid = await _seed_tenant(admin_engine)
    async with tenant_session(tid) as s:
        await append_entry(s, tenant_id=tid, event_type="a")
        await append_entry(s, tenant_id=tid, event_type="b")
        await append_entry(s, tenant_id=tid, event_type="c")
    factory = async_sessionmaker(bind=admin_engine, expire_on_commit=False, autoflush=False)
    async with factory() as s, s.begin():
        await s.execute(
            text("DELETE FROM audit_log_entry WHERE tenant_id = :tid AND sequence = 2"),
            {"tid": str(tid)},
        )
    async with tenant_session(tid) as s:
        with pytest.raises(AuditChainBrokenError):
            await verify_chain(s, tid)


async def test_sequence_numbering_is_per_tenant(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    t1 = await _seed_tenant(admin_engine, name="t1")
    t2 = await _seed_tenant(admin_engine, name="t2")
    async with tenant_session(t1) as s:
        e1_a = await append_entry(s, tenant_id=t1, event_type="a")
    async with tenant_session(t2) as s:
        e2_a = await append_entry(s, tenant_id=t2, event_type="a")
    async with tenant_session(t1) as s:
        e1_b = await append_entry(s, tenant_id=t1, event_type="b")
    assert e1_a.sequence == 1
    assert e2_a.sequence == 1
    assert e1_b.sequence == 2
    assert e1_b.previous_entry_hash == e1_a.entry_hash
