# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from pydantic import Field, field_validator

from shared.fingerprint.features import FINGERPRINT_DIM
from shared.fingerprint.repository import FingerprintNeighbor
from shared.graph.views import ContactGraphView
from shared.schemas.base import FrozenModel


class ContactGraphLookupRequest(FrozenModel):
    tenant_id: UUID
    actor_id: UUID
    lookback_days: int = Field(default=7, ge=1, le=90)


class ContactGraphLookupResponse(FrozenModel):
    view: ContactGraphView


class FingerprintUpsertRequest(FrozenModel):
    tenant_id: UUID
    actor_id: UUID
    vector: tuple[float, ...]
    flagged: bool

    @field_validator("vector")
    @classmethod
    def _check_dim(cls, v: tuple[float, ...]) -> tuple[float, ...]:
        if len(v) != FINGERPRINT_DIM:
            raise ValueError(f"vector must have {FINGERPRINT_DIM} dims")
        return v


class FingerprintSimilarRequest(FrozenModel):
    tenant_id: UUID
    actor_id: UUID
    vector: tuple[float, ...]
    top_k: int = Field(default=10, ge=1, le=100)

    @field_validator("vector")
    @classmethod
    def _check_dim(cls, v: tuple[float, ...]) -> tuple[float, ...]:
        if len(v) != FINGERPRINT_DIM:
            raise ValueError(f"vector must have {FINGERPRINT_DIM} dims")
        return v


class FingerprintSimilarResponse(FrozenModel):
    neighbors: tuple[FingerprintNeighbor, ...] = ()
