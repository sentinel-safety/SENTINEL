# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.response.retry import next_retry_delay

pytestmark = pytest.mark.unit


def test_first_attempt_uses_base() -> None:
    assert next_retry_delay(attempt=1, base=2.0, cap=60.0) == 2.0


def test_second_attempt_doubles() -> None:
    assert next_retry_delay(attempt=2, base=2.0, cap=60.0) == 4.0


def test_fifth_attempt_still_exponential() -> None:
    assert next_retry_delay(attempt=5, base=2.0, cap=60.0) == 32.0


def test_cap_applies() -> None:
    assert next_retry_delay(attempt=10, base=2.0, cap=60.0) == 60.0


def test_attempt_zero_invalid() -> None:
    with pytest.raises(ValueError):
        next_retry_delay(attempt=0, base=2.0, cap=60.0)
