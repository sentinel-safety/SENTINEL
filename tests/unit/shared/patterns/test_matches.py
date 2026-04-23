# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.patterns.matches import DetectionMode, PatternMatch
from shared.scoring.signals import SignalKind

pytestmark = pytest.mark.unit


def test_detection_mode_values() -> None:
    assert {m.value for m in DetectionMode} == {"rule", "llm"}


def test_pattern_match_requires_confidence_in_unit_interval() -> None:
    with pytest.raises(ValueError):
        PatternMatch(
            pattern_name="secrecy_request",
            signal_kind=SignalKind.SECRECY_REQUEST,
            confidence=1.5,
            evidence_excerpts=("don't tell your parents",),
            detection_mode=DetectionMode.RULE,
            prompt_version=None,
        )


def test_pattern_match_is_frozen() -> None:
    match = PatternMatch(
        pattern_name="secrecy_request",
        signal_kind=SignalKind.SECRECY_REQUEST,
        confidence=0.9,
        evidence_excerpts=("don't tell",),
        detection_mode=DetectionMode.RULE,
        prompt_version=None,
    )
    with pytest.raises(ValueError):
        match.confidence = 0.1  # type: ignore[misc]


def test_pattern_match_llm_requires_prompt_version() -> None:
    with pytest.raises(ValueError):
        PatternMatch(
            pattern_name="friendship_forming",
            signal_kind=SignalKind.FRIENDSHIP_FORMING,
            confidence=0.7,
            evidence_excerpts=("you're the best",),
            detection_mode=DetectionMode.LLM,
            prompt_version=None,
        )


def test_pattern_match_rule_rejects_prompt_version() -> None:
    with pytest.raises(ValueError):
        PatternMatch(
            pattern_name="secrecy_request",
            signal_kind=SignalKind.SECRECY_REQUEST,
            confidence=1.0,
            evidence_excerpts=("don't tell",),
            detection_mode=DetectionMode.RULE,
            prompt_version="v1",
        )


def test_evidence_excerpts_is_tuple_of_str() -> None:
    match = PatternMatch(
        pattern_name="secrecy_request",
        signal_kind=SignalKind.SECRECY_REQUEST,
        confidence=0.9,
        evidence_excerpts=("a", "b"),
        detection_mode=DetectionMode.RULE,
        prompt_version=None,
    )
    assert isinstance(match.evidence_excerpts, tuple)
    assert match.evidence_excerpts == ("a", "b")
