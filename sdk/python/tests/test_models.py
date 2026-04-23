from __future__ import annotations

import pytest

from sentinel.models import (
    ActionKind,
    EventType,
    PrimaryDriver,
    Reasoning,
    RecommendedAction,
    ResponseTier,
    ScoreResult,
)


def test_event_type_values() -> None:
    assert EventType.MESSAGE.value == "message"
    assert EventType.IMAGE.value == "image"
    assert EventType.FRIEND_REQUEST.value == "friend_request"
    assert EventType.GIFT.value == "gift"
    assert EventType.PROFILE_CHANGE.value == "profile_change"
    assert EventType.VOICE_CLIP.value == "voice_clip"


def test_response_tier_is_ordered_intenum() -> None:
    assert int(ResponseTier.TRUSTED) == 0
    assert int(ResponseTier.CRITICAL) == 5
    assert ResponseTier.WATCH < ResponseTier.THROTTLE


def test_score_result_parses_tier_from_string() -> None:
    result = ScoreResult.model_validate(
        {
            "current_score": 42,
            "previous_score": 30,
            "delta": 12,
            "tier": "watch",
            "reasoning": None,
        }
    )
    assert result.tier is ResponseTier.WATCH
    assert result.delta == 12


def test_score_result_serializes_tier_as_lowercase() -> None:
    result = ScoreResult(
        current_score=10, previous_score=0, delta=10, tier=ResponseTier.TRUSTED, reasoning=None
    )
    assert result.model_dump()["tier"] == "trusted"


def test_score_result_rejects_out_of_range_score() -> None:
    with pytest.raises(ValueError):
        ScoreResult(
            current_score=999, previous_score=0, delta=0, tier=ResponseTier.TRUSTED, reasoning=None
        )


def test_reasoning_round_trip() -> None:
    payload = {
        "actor_id": "00000000-0000-0000-0000-000000000001",
        "tenant_id": "00000000-0000-0000-0000-000000000002",
        "score_change": 12,
        "new_score": 42,
        "new_tier": "watch",
        "primary_drivers": [
            {
                "pattern": "Late-night contact",
                "pattern_id": "late_night",
                "confidence": 0.82,
                "evidence": "Contact occurred at 2:14 AM local time",
            }
        ],
        "context": "Third escalation in 72 hours",
        "recommended_action_summary": "Monitor additional contact",
        "generated_at": "2026-04-20T12:00:00+00:00",
        "next_review_at": None,
    }
    reasoning = Reasoning.model_validate(payload)
    assert len(reasoning.primary_drivers) == 1
    assert reasoning.primary_drivers[0].pattern_id == "late_night"


def test_recommended_action_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError):
        RecommendedAction.model_validate({"kind": "bogus", "description": "x"})


def test_action_kind_exposes_all_members() -> None:
    assert ActionKind.NONE.value == "none"
    assert ActionKind.MANDATORY_REPORT.value == "mandatory_report"


def test_primary_driver_rejects_confidence_above_one() -> None:
    with pytest.raises(ValueError):
        PrimaryDriver(pattern="x", pattern_id="x", confidence=1.5, evidence="x")
