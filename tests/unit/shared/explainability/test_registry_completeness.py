# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from services.patterns.app.registry import SYNC_PATTERNS, build_llm_patterns
from shared.explainability.evidence_templates import EVIDENCE_TEMPLATES
from shared.explainability.pattern_display_names import PATTERN_DISPLAY_NAMES
from shared.llm import FakeProvider

pytestmark = pytest.mark.unit


def _all_pattern_names() -> set[str]:
    names: set[str] = set()
    for sync_pattern in SYNC_PATTERNS:
        names.add(sync_pattern.name)
    for llm_pattern in build_llm_patterns(FakeProvider(responses={})):
        names.add(llm_pattern.name)
    names.add("sexual_escalation:photo_request")
    names.add("sexual_escalation:video_request")
    names.add("federation_signal_match")
    return names


def test_every_pattern_has_evidence_template() -> None:
    missing = _all_pattern_names() - set(EVIDENCE_TEMPLATES)
    assert not missing, f"patterns missing evidence template: {sorted(missing)}"


def test_every_pattern_has_display_name() -> None:
    missing = _all_pattern_names() - set(PATTERN_DISPLAY_NAMES)
    assert not missing, f"patterns missing display name: {sorted(missing)}"


def test_no_orphan_templates() -> None:
    orphan = set(EVIDENCE_TEMPLATES) - _all_pattern_names()
    assert not orphan, f"evidence templates without registered pattern: {sorted(orphan)}"


def test_no_orphan_display_names() -> None:
    orphan = set(PATTERN_DISPLAY_NAMES) - _all_pattern_names()
    assert not orphan, f"display names without registered pattern: {sorted(orphan)}"
