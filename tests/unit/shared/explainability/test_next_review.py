# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from shared.explainability.next_review import compute_next_review_at
from shared.schemas.enums import ResponseTier

pytestmark = pytest.mark.unit


def test_trusted_returns_none() -> None:
    now = datetime.now(UTC)
    assert compute_next_review_at(ResponseTier.TRUSTED, now=now) is None


def test_watch_returns_none() -> None:
    now = datetime.now(UTC)
    assert compute_next_review_at(ResponseTier.WATCH, now=now) is None


def test_active_monitor_returns_72h() -> None:
    now = datetime.now(UTC)
    assert compute_next_review_at(ResponseTier.ACTIVE_MONITOR, now=now) == now + timedelta(hours=72)


def test_throttle_returns_24h() -> None:
    now = datetime.now(UTC)
    assert compute_next_review_at(ResponseTier.THROTTLE, now=now) == now + timedelta(hours=24)


def test_restrict_returns_24h() -> None:
    now = datetime.now(UTC)
    assert compute_next_review_at(ResponseTier.RESTRICT, now=now) == now + timedelta(hours=24)


def test_critical_returns_24h() -> None:
    now = datetime.now(UTC)
    assert compute_next_review_at(ResponseTier.CRITICAL, now=now) == now + timedelta(hours=24)
