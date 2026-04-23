# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import struct
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models import FederationSignal
from shared.schemas.base import FrozenModel


class StoredFederationSignal(FrozenModel):
    id: UUID
    publisher_tenant_id: UUID
    fingerprint: tuple[float, ...]
    signal_kinds: tuple[str, ...]
    flagged_at: datetime
    commit: bytes


def _bytes_to_floats(raw: bytes) -> tuple[float, ...]:
    count = len(raw) // 4
    return struct.unpack(f"{count}f", raw[: count * 4])


def _floats_to_bytes(vec: tuple[float, ...]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


async def insert_signal(
    session: AsyncSession,
    *,
    publisher_tenant_id: UUID,
    fingerprint_bytes: bytes,
    signal_kinds: tuple[str, ...],
    flagged_at: datetime,
    commit: bytes,
) -> UUID:
    signal = FederationSignal(
        publisher_tenant_id=publisher_tenant_id,
        fingerprint=fingerprint_bytes,
        signal_kinds=list(signal_kinds),
        flagged_at=flagged_at,
        commit=commit,
    )
    session.add(signal)
    await session.flush()
    return signal.id


async def list_recent(
    session: AsyncSession,
    *,
    limit: int = 100,
) -> tuple[StoredFederationSignal, ...]:
    result = await session.execute(
        select(FederationSignal).order_by(FederationSignal.received_at.desc()).limit(limit)
    )
    rows = result.scalars().all()
    return tuple(
        StoredFederationSignal(
            id=r.id,
            publisher_tenant_id=r.publisher_tenant_id,
            fingerprint=_bytes_to_floats(r.fingerprint),
            signal_kinds=tuple(r.signal_kinds),
            flagged_at=r.flagged_at,
            commit=r.commit,
        )
        for r in rows
    )
