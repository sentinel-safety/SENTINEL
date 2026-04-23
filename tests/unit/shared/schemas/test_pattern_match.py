# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from shared.schemas import GroomingStage, PatternMatch

pytestmark = pytest.mark.unit


def _make_match(**overrides: object) -> PatternMatch:
    defaults = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "actor_id": uuid4(),
        "pattern_id": "platform_migration_request",
        "pattern_version": "1.0.0",
        "confidence": 0.91,
        "event_ids": (uuid4(),),
        "matched_at": datetime.now(UTC),
        "evidence_summary": "Actor asked target to move to Telegram three times.",
    }
    return PatternMatch.model_validate({**defaults, **overrides})


def test_confidence_is_bounded() -> None:
    with pytest.raises(ValidationError):
        _make_match(confidence=-0.01)
    with pytest.raises(ValidationError):
        _make_match(confidence=1.01)


def test_event_ids_must_be_non_empty() -> None:
    with pytest.raises(ValidationError):
        _make_match(event_ids=())


def test_stage_optional_defaults_none() -> None:
    m = _make_match()
    assert m.stage is None


def test_stage_roundtrip() -> None:
    m = _make_match(stage=GroomingStage.ISOLATION)
    restored = PatternMatch.model_validate(m.model_dump(mode="json"))
    assert restored.stage == GroomingStage.ISOLATION
