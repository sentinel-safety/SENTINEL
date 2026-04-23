# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from services.patterns.app.registry import LLM_PATTERNS, SYNC_PATTERNS
from shared.patterns.matches import DetectionMode

pytestmark = pytest.mark.unit


def test_registries_are_tuples() -> None:
    assert isinstance(SYNC_PATTERNS, tuple)
    assert isinstance(LLM_PATTERNS, tuple)


def test_sync_patterns_all_rule_mode() -> None:
    for pattern in SYNC_PATTERNS:
        assert pattern.mode is DetectionMode.RULE


def test_llm_patterns_all_llm_mode() -> None:
    for pattern in LLM_PATTERNS:
        assert pattern.mode is DetectionMode.LLM


def test_no_duplicate_names() -> None:
    sync_names = [p.name for p in SYNC_PATTERNS]
    llm_names = [p.name for p in LLM_PATTERNS]
    all_names = sync_names + llm_names
    assert len(all_names) == len(set(all_names))


def test_total_pattern_count_is_17() -> None:
    assert len(SYNC_PATTERNS) + len(LLM_PATTERNS) == 17


def test_scaffolded_patterns_present() -> None:
    sync_names = {p.name for p in SYNC_PATTERNS}
    assert "age_incongruence" in sync_names
    assert "behavioral_fingerprint_match" in sync_names
