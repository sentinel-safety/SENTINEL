# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from shared.config import get_settings


def build_hasher(
    *,
    time_cost: int | None = None,
    memory_cost: int | None = None,
    parallelism: int | None = None,
) -> PasswordHasher:
    settings = get_settings()
    return PasswordHasher(
        time_cost=time_cost if time_cost is not None else settings.dashboard_argon2_time_cost,
        memory_cost=(
            memory_cost if memory_cost is not None else settings.dashboard_argon2_memory_cost
        ),
        parallelism=(
            parallelism if parallelism is not None else settings.dashboard_argon2_parallelism
        ),
    )


def hash_password(password: str, *, hasher: PasswordHasher | None = None) -> str:
    if not password:
        raise ValueError("password must not be empty")
    return (hasher or build_hasher()).hash(password)


def verify_password(password: str, digest: str, *, hasher: PasswordHasher | None = None) -> bool:
    try:
        return (hasher or build_hasher()).verify(digest, password)
    except VerifyMismatchError:
        return False
