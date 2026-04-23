# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations


def next_retry_delay(*, attempt: int, base: float, cap: float) -> float:
    if attempt < 1:
        raise ValueError("attempt must be >= 1")
    unbounded: float = base * (2 ** (attempt - 1))
    return unbounded if unbounded < cap else cap
