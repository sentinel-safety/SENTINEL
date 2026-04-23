# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

import orjson
from pydantic import field_validator

from shared.schemas.base import FrozenModel

SIGNAL_FIELDS_CANONICAL_ORDER = (
    "actor_hash",
    "flagged_at",
    "fingerprint",
    "publisher_tenant_id",
    "schema_version",
    "signal_kinds",
)


class FederationSignal(FrozenModel):
    publisher_tenant_id: UUID
    actor_hash: bytes
    fingerprint: tuple[float, ...]
    signal_kinds: tuple[str, ...]
    flagged_at: datetime
    schema_version: Literal[1] = 1

    @field_validator("fingerprint")
    @classmethod
    def _fingerprint_dim(cls, v: tuple[float, ...]) -> tuple[float, ...]:
        if len(v) != 16:
            raise ValueError(f"fingerprint must have 16 dimensions, got {len(v)}")
        return v

    @field_validator("signal_kinds")
    @classmethod
    def _signal_kinds_non_empty(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        if not v:
            raise ValueError("signal_kinds must be non-empty")
        return v

    @field_validator("flagged_at")
    @classmethod
    def _require_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("flagged_at must be timezone-aware")
        return v.astimezone(UTC)


class FederationSignalEnvelope(FrozenModel):
    signal: FederationSignal
    commit: bytes


def canonical_bytes(signal: FederationSignal) -> bytes:
    data = {
        "actor_hash": signal.actor_hash.hex(),
        "flagged_at": signal.flagged_at.isoformat(),
        "fingerprint": list(signal.fingerprint),
        "publisher_tenant_id": str(signal.publisher_tenant_id),
        "schema_version": signal.schema_version,
        "signal_kinds": sorted(signal.signal_kinds),
    }
    return orjson.dumps(data, option=orjson.OPT_SORT_KEYS)
