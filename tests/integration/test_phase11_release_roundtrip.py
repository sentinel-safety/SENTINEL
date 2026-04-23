# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import orjson
import pytest

from services.patterns.app.library.secrecy_request import SecrecyRequestPattern
from shared.llm.fake import FakeProvider
from shared.synthetic.axes import (
    CommunicationStyle,
    Demographics,
    DiversityAxes,
    GroomingStage,
    Platform,
    StageMix,
)
from shared.synthetic.pipeline import generate_dataset
from shared.synthetic.release import build_release_artifact
from shared.synthetic.stages import STAGE_PROMPTS
from shared.synthetic.validation import (
    MockRealDatasetAdapter,
    ReferenceConversation,
    validate_against_baseline,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def _fake_provider() -> FakeProvider:
    return FakeProvider(
        responses={
            prompt: {"text": f"don't tell your parents — safe cue for {stage.value}"}
            for stage, prompt in STAGE_PROMPTS.items()
        }
    )


def _make_axes() -> DiversityAxes:
    return DiversityAxes(
        demographics=(Demographics(age_band="14-15", gender="male", regional_context="UK"),),
        platforms=(Platform.DM,),
        communication_styles=(CommunicationStyle.CASUAL_TYPING,),
        languages=("en",),
    )


def _make_stage_mix() -> StageMix:
    return StageMix(weights=dict.fromkeys(GroomingStage, 1))


def _make_real_adapter() -> MockRealDatasetAdapter:
    stages = list(GroomingStage)
    refs = tuple(
        ReferenceConversation(
            id=i,
            stage=stages[i % len(stages)],
            turns=("don't tell your parents — safe cue", "ok"),
            label=True,
        )
        for i in range(20)
    )
    return MockRealDatasetAdapter(refs)


async def test_release_roundtrip_generate_build_validate(tmp_path: Path) -> None:
    provider = _fake_provider()
    axes = _make_axes()
    stage_mix = _make_stage_mix()

    dataset = await generate_dataset(
        axes=axes,
        stage_mix=stage_mix,
        count=20,
        seed=42,
        provider=provider,
    )
    assert len(dataset.conversations) == 20
    assert dataset.seed == 42

    manifest = build_release_artifact(dataset, tmp_path)

    assert (tmp_path / "conversations.jsonl").exists()
    assert (tmp_path / "LICENSE").exists()
    assert (tmp_path / "DATASHEET.md").exists()
    assert (tmp_path / "manifest.json").exists()

    jsonl_bytes = (tmp_path / "conversations.jsonl").read_bytes()
    expected_sha = sha256(jsonl_bytes).hexdigest()
    assert manifest.sha256_conversations == expected_sha

    manifest_data = orjson.loads((tmp_path / "manifest.json").read_bytes())
    assert manifest_data["schema_version"] == 1
    assert manifest_data["sha256_conversations"] == expected_sha
    assert manifest_data["conversation_count"] == 20

    patterns = [SecrecyRequestPattern()]
    report = await validate_against_baseline(dataset, _make_real_adapter(), patterns)
    assert report.parity_achieved is True
