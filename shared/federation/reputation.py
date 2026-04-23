# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from enum import IntEnum


class ReputationDelta(IntEnum):
    CONFIRM_TRUE = 1
    CONFIRM_FALSE = -5
    EXPLICIT_COMPLAINT = -10
    SIGNATURE_INVALID = -2


def adjust_reputation(current: int, event_kind: str) -> int:
    delta = ReputationDelta[event_kind].value
    return max(0, min(100, current + delta))
