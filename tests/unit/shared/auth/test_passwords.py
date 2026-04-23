# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from argon2 import PasswordHasher

from shared.auth.passwords import build_hasher, hash_password, verify_password

pytestmark = pytest.mark.unit


def _fast_hasher() -> PasswordHasher:
    return build_hasher(time_cost=1, memory_cost=8, parallelism=1)


def test_hash_then_verify_round_trip() -> None:
    hasher = _fast_hasher()
    digest = hash_password("correct horse battery staple", hasher=hasher)
    assert digest.startswith("$argon2id$")
    assert verify_password("correct horse battery staple", digest, hasher=hasher) is True


def test_verify_rejects_wrong_password() -> None:
    hasher = _fast_hasher()
    digest = hash_password("right", hasher=hasher)
    assert verify_password("wrong", digest, hasher=hasher) is False


def test_hashes_differ_between_calls() -> None:
    hasher = _fast_hasher()
    a = hash_password("same", hasher=hasher)
    b = hash_password("same", hasher=hasher)
    assert a != b
    assert verify_password("same", a, hasher=hasher) is True
    assert verify_password("same", b, hasher=hasher) is True


def test_rejects_empty_password() -> None:
    hasher = _fast_hasher()
    with pytest.raises(ValueError):
        hash_password("", hasher=hasher)
