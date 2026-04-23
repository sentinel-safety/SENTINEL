# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Any

import pytest

from shared.llm.fake import FakeProvider
from shared.synthetic.axes import (
    CommunicationStyle,
    Demographics,
    DiversityAxes,
    GroomingStage,
    Platform,
    StageMix,
)
from shared.synthetic.pipeline import FORBIDDEN_TOKENS, contains_forbidden_content, generate_dataset
from shared.synthetic.stages import STAGE_PROMPTS

pytestmark = pytest.mark.unit


def test_forbidden_tokens_nonempty() -> None:
    assert len(FORBIDDEN_TOKENS) > 0


def test_contains_forbidden_content_clean() -> None:
    assert not contains_forbidden_content("you seem really mature for your age")


def test_contains_forbidden_content_detects_explicit() -> None:
    for token in list(FORBIDDEN_TOKENS)[:3]:
        assert contains_forbidden_content(f"some text with {token} in it")


async def test_forbidden_response_replaced_with_fallback() -> None:
    bad_token = next(iter(FORBIDDEN_TOKENS))

    responses: dict[str, dict[str, Any]] = {}
    for stage, prompt in STAGE_PROMPTS.items():
        responses[prompt] = {"text": f"safe reply for {stage.value}"}

    first_prompt = next(iter(STAGE_PROMPTS.values()))
    responses[first_prompt] = {"text": f"explicit {bad_token} content"}

    provider = FakeProvider(responses=responses)
    axes = DiversityAxes(
        demographics=(Demographics(age_band="14-15", gender="male", regional_context="UK"),),
        platforms=(Platform.DM,),
        communication_styles=(CommunicationStyle.CASUAL_TYPING,),
        languages=("en",),
    )
    mix = StageMix(weights={next(iter(GroomingStage)): 1})
    ds = await generate_dataset(axes=axes, stage_mix=mix, count=1, seed=0, provider=provider)
    for conv in ds.conversations:
        for turn in conv.turns:
            assert not contains_forbidden_content(turn.text)
