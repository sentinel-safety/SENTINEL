# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from shared.schemas import Actor, AgeBand

pytestmark = pytest.mark.unit


def _make_actor(**overrides: object) -> Actor:
    defaults = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "external_id_hash": "a" * 64,
        "account_created_at": datetime.now(UTC),
    }
    return Actor.model_validate({**defaults, **overrides})


def test_actor_defaults() -> None:
    a = _make_actor()
    assert a.claimed_age_band == AgeBand.UNKNOWN
    assert a.metadata == {}


def test_external_id_hash_must_be_sha256_hex() -> None:
    with pytest.raises(ValidationError):
        _make_actor(external_id_hash="nothex!")
    with pytest.raises(ValidationError):
        _make_actor(external_id_hash="a" * 63)
    with pytest.raises(ValidationError):
        _make_actor(external_id_hash="A" * 64)


@pytest.mark.parametrize(
    ("band", "expected"),
    [
        (AgeBand.UNDER_13, True),
        (AgeBand.BAND_13_15, True),
        (AgeBand.BAND_16_17, True),
        (AgeBand.ADULT, False),
        (AgeBand.UNKNOWN, False),
    ],
)
def test_is_minor_matches_age_band(band: AgeBand, expected: bool) -> None:
    a = _make_actor(claimed_age_band=band)
    assert a.is_minor is expected


def test_metadata_accepts_arbitrary_json() -> None:
    a = _make_actor(metadata={"region": "EU", "locale": "en-GB", "premium": True})
    assert a.metadata["premium"] is True


def test_actor_is_frozen() -> None:
    a = _make_actor()
    with pytest.raises(ValidationError):
        a.tenant_id = uuid4()  # type: ignore[misc]
