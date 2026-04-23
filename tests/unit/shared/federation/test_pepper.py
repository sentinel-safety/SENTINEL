# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from shared.federation.pepper import hash_actor

pytestmark = pytest.mark.unit

_PEPPER = b"test-pepper-32-bytes-padding!!!!!"
_ACTOR_ID = UUID("12345678-1234-5678-1234-567812345678")


def test_hash_actor_returns_32_bytes() -> None:
    result = hash_actor(actor_id=_ACTOR_ID, pepper=_PEPPER)
    assert isinstance(result, bytes)
    assert len(result) == 32


def test_hash_actor_is_deterministic() -> None:
    assert hash_actor(actor_id=_ACTOR_ID, pepper=_PEPPER) == hash_actor(
        actor_id=_ACTOR_ID, pepper=_PEPPER
    )


def test_different_peppers_produce_different_hashes() -> None:
    h1 = hash_actor(actor_id=_ACTOR_ID, pepper=b"pepper-one-32-bytes-padding!!!!!")
    h2 = hash_actor(actor_id=_ACTOR_ID, pepper=b"pepper-two-32-bytes-padding!!!!!")
    assert h1 != h2


def test_different_actors_produce_different_hashes() -> None:
    h1 = hash_actor(actor_id=uuid4(), pepper=_PEPPER)
    h2 = hash_actor(actor_id=uuid4(), pepper=_PEPPER)
    assert h1 != h2
