# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from shared.explainability.evidence_templates import render_evidence
from shared.explainability.pattern_display_names import PATTERN_DISPLAY_NAMES
from shared.patterns.matches import PatternMatch
from shared.schemas.reasoning import PrimaryDriver
from shared.scoring.deltas import DELTA_BY_SIGNAL

_MAX_DRIVERS: int = 3


def _weight(match: PatternMatch) -> float:
    delta = abs(DELTA_BY_SIGNAL.get(match.signal_kind, 0))
    return delta * match.confidence


def _to_driver(match: PatternMatch) -> PrimaryDriver:
    evidence = render_evidence(
        pattern_name=match.pattern_name,
        variables=dict(match.template_variables),
    )
    return PrimaryDriver(
        pattern=PATTERN_DISPLAY_NAMES[match.pattern_name],
        pattern_id=match.pattern_name,
        confidence=match.confidence,
        evidence=evidence,
    )


def rank_primary_drivers(matches: tuple[PatternMatch, ...]) -> tuple[PrimaryDriver, ...]:
    ordered = sorted(matches, key=lambda m: (-_weight(m), -m.confidence))
    return tuple(_to_driver(m) for m in ordered[:_MAX_DRIVERS])
