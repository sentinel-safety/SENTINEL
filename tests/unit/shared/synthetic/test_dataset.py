# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from shared.synthetic.axes import (
    CommunicationStyle,
    Demographics,
    DiversityAxes,
    GroomingStage,
    Platform,
    StageMix,
)
from shared.synthetic.dataset import SyntheticConversation, SyntheticDataset, SyntheticTurn

pytestmark = pytest.mark.unit


def _turn(role: str = "actor", text: str = "hello", offset: int = 0) -> SyntheticTurn:
    return SyntheticTurn(role=role, text=text, timestamp_offset_seconds=offset)


def _conversation() -> SyntheticConversation:
    return SyntheticConversation(
        id=uuid4(),
        stage=GroomingStage.FRIENDSHIP_FORMING,
        demographics=Demographics(age_band="14-15", gender="male", regional_context="UK"),
        platform=Platform.DM,
        communication_style=CommunicationStyle.CASUAL_TYPING,
        language="en",
        turns=(_turn("actor", "you seem cool", 0), _turn("target", "thanks", 10)),
    )


def _default_dataset() -> SyntheticDataset:
    axes = DiversityAxes(
        demographics=(Demographics(age_band="14-15", gender="male", regional_context="UK"),),
        platforms=(Platform.DM,),
        communication_styles=(CommunicationStyle.CASUAL_TYPING,),
        languages=("en",),
    )
    mix = StageMix(weights={GroomingStage.FRIENDSHIP_FORMING: 1})
    return SyntheticDataset(
        run_id=uuid4(),
        seed=42,
        axes=axes,
        stage_mix=mix,
        conversations=(_conversation(),),
        generated_at=datetime.now(UTC),
    )


def test_synthetic_turn_round_trip() -> None:
    t = _turn("actor", "hello world", 5)
    restored = SyntheticTurn.model_validate(t.model_dump())
    assert restored == t


def test_synthetic_turn_text_max_length_enforced() -> None:
    with pytest.raises(ValidationError):
        _turn(text="x" * 2001)


def test_synthetic_turn_invalid_role() -> None:
    with pytest.raises(ValidationError):
        SyntheticTurn(role="unknown", text="hi", timestamp_offset_seconds=0)


def test_synthetic_conversation_round_trip() -> None:
    c = _conversation()
    restored = SyntheticConversation.model_validate(c.model_dump())
    assert restored == c


def test_synthetic_conversation_requires_two_turns() -> None:
    with pytest.raises(ValidationError):
        SyntheticConversation(
            id=uuid4(),
            stage=GroomingStage.ISOLATION,
            demographics=Demographics(age_band="14-15", gender="male", regional_context="UK"),
            platform=Platform.DM,
            communication_style=CommunicationStyle.CASUAL_TYPING,
            language="en",
            turns=(_turn(),),
        )


def test_synthetic_dataset_round_trip() -> None:
    ds = _default_dataset()
    restored = SyntheticDataset.model_validate(ds.model_dump())
    assert restored.run_id == ds.run_id
    assert restored.seed == ds.seed
    assert restored.schema_version == 1


def test_synthetic_dataset_empty_conversations_rejected() -> None:
    axes = DiversityAxes(
        demographics=(Demographics(age_band="14-15", gender="male", regional_context="UK"),),
        platforms=(Platform.DM,),
        communication_styles=(CommunicationStyle.CASUAL_TYPING,),
        languages=("en",),
    )
    with pytest.raises(ValidationError):
        SyntheticDataset(
            run_id=uuid4(),
            seed=42,
            axes=axes,
            stage_mix=StageMix(weights={GroomingStage.FRIENDSHIP_FORMING: 1}),
            conversations=(),
            generated_at=datetime.now(UTC),
        )
