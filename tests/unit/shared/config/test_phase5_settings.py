# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.config.settings import Settings

pytestmark = pytest.mark.unit


def test_tier_change_stream_default() -> None:
    assert Settings().response_tier_change_stream == "response:tier_changes"


def test_retry_stream_default() -> None:
    assert Settings().response_retry_stream == "response:retry_queue"


def test_dead_letter_stream_default() -> None:
    assert Settings().response_dead_letter_stream == "response:dead_letter"


def test_retry_policy_defaults() -> None:
    s = Settings()
    assert s.response_retry_max_attempts == 5
    assert s.response_retry_base_delay_seconds == 2.0
    assert s.response_retry_max_delay_seconds == 60.0


def test_hmac_skew_default() -> None:
    assert Settings().response_hmac_timestamp_skew_seconds == 300


def test_response_base_url_default() -> None:
    assert Settings().response_base_url == "http://127.0.0.1:8007"


def test_worker_block_ms_default() -> None:
    assert Settings().response_worker_block_ms == 2000
