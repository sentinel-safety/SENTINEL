# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.explainability.primary_drivers import rank_primary_drivers
from shared.patterns.matches import DetectionMode, PatternMatch
from shared.scoring.signals import SignalKind

pytestmark = pytest.mark.unit


def _m(
    name: str,
    kind: SignalKind,
    confidence: float,
    excerpt: str = "x",
) -> PatternMatch:
    return PatternMatch(
        pattern_name=name,
        signal_kind=kind,
        confidence=confidence,
        evidence_excerpts=(excerpt,),
        detection_mode=DetectionMode.RULE,
        prompt_version=None,
        template_variables={"matched_phrase": excerpt},
    )


def test_empty_matches_returns_empty() -> None:
    assert rank_primary_drivers(()) == ()


def test_ranks_by_delta_times_confidence() -> None:
    matches = (
        _m("late_night", SignalKind.LATE_NIGHT_MINOR_CONTACT, 1.0),
        _m(
            "platform_migration",
            SignalKind.PLATFORM_MIGRATION_REQUEST,
            0.5,
            excerpt="let's move to telegram",
        ),
    )
    drivers = rank_primary_drivers(matches)
    assert drivers[0].pattern_id == "platform_migration"
    assert drivers[0].pattern == "Platform Migration Request"


def test_caps_at_three() -> None:
    matches = tuple(
        _m("secrecy_request", SignalKind.SECRECY_REQUEST, 1.0 - i * 0.01, excerpt=f"p{i}")
        for i in range(5)
    )
    drivers = rank_primary_drivers(matches)
    assert len(drivers) == 3


def test_ties_break_on_confidence() -> None:
    a = _m("exclusivity", SignalKind.EXCLUSIVITY, 0.8)
    b = _m("exclusivity", SignalKind.EXCLUSIVITY, 0.9)
    drivers = rank_primary_drivers((a, b))
    assert drivers[0].confidence == pytest.approx(0.9)


def test_driver_evidence_is_rendered_not_excerpt_only() -> None:
    match = _m(
        "platform_migration",
        SignalKind.PLATFORM_MIGRATION_REQUEST,
        0.91,
        excerpt="let's move to telegram",
    )
    drivers = rank_primary_drivers((match,))
    assert "telegram" in drivers[0].evidence.lower()
    assert len(drivers[0].evidence) >= len("let's move to telegram")
