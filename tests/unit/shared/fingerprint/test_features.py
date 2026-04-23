# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.fingerprint.features import (
    FINGERPRINT_DIM,
    ActorFeatureWindow,
    FingerprintVector,
    compute_fingerprint,
)

pytestmark = pytest.mark.unit


def test_fingerprint_dim_is_sixteen() -> None:
    assert FINGERPRINT_DIM == 16


def _window(**overrides: float) -> ActorFeatureWindow:
    base: dict[str, float] = {
        "total_messages": 10.0,
        "compliment_count": 2.0,
        "question_count": 4.0,
        "personal_info_requests": 1.0,
        "late_night_count": 3.0,
        "minor_recipient_count": 6.0,
        "platform_migration_mentions": 0.0,
        "secrecy_mentions": 0.0,
        "distinct_minor_targets": 2.0,
        "total_chars": 500.0,
        "distinct_conversations": 3.0,
        "url_mentions": 0.0,
        "gift_mentions": 0.0,
        "image_requests": 0.0,
        "video_requests": 0.0,
        "contact_requests": 1.0,
    }
    base.update(overrides)
    return ActorFeatureWindow(**base)


def test_compute_fingerprint_has_fixed_dimension() -> None:
    fp = compute_fingerprint(_window())
    assert len(fp) == FINGERPRINT_DIM


def test_compute_fingerprint_is_deterministic() -> None:
    w = _window()
    assert compute_fingerprint(w) == compute_fingerprint(w)


def test_compute_fingerprint_is_l2_normalized() -> None:
    fp = compute_fingerprint(_window())
    l2 = sum(x * x for x in fp) ** 0.5
    assert l2 == pytest.approx(1.0, rel=1e-6)


def test_compute_fingerprint_handles_zero_messages() -> None:
    fp = compute_fingerprint(_window(total_messages=0.0))
    assert len(fp) == FINGERPRINT_DIM
    assert all(x == 0.0 for x in fp)


def test_fingerprint_vector_rejects_wrong_dim() -> None:
    with pytest.raises(ValueError):
        FingerprintVector(values=tuple(0.0 for _ in range(FINGERPRINT_DIM - 1)))


def test_different_inputs_produce_different_fingerprints() -> None:
    a = compute_fingerprint(_window(secrecy_mentions=5.0))
    b = compute_fingerprint(_window(secrecy_mentions=0.0))
    assert a != b
