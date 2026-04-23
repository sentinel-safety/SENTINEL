# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import orjson
import pytest

from shared.synthetic.axes import (
    CommunicationStyle,
    Demographics,
    DiversityAxes,
    GroomingStage,
    Platform,
    StageMix,
)
from shared.synthetic.dataset import SyntheticConversation, SyntheticDataset, SyntheticTurn
from shared.synthetic.release import build_release_artifact

pytestmark = pytest.mark.unit


def _make_dataset(count: int = 3) -> SyntheticDataset:
    axes = DiversityAxes(
        demographics=(Demographics(age_band="14-15", gender="male", regional_context="UK"),),
        platforms=(Platform.DM,),
        communication_styles=(CommunicationStyle.CASUAL_TYPING,),
        languages=("en",),
    )
    stage_mix = StageMix(weights={GroomingStage.ISOLATION: 1})
    turns = (
        SyntheticTurn(role="actor", text="don't tell anyone", timestamp_offset_seconds=0),
        SyntheticTurn(role="target", text="ok", timestamp_offset_seconds=15),
    )
    convs = tuple(
        SyntheticConversation(
            id=uuid4(),
            stage=GroomingStage.ISOLATION,
            demographics=Demographics(age_band="14-15", gender="male", regional_context="UK"),
            platform=Platform.DM,
            communication_style=CommunicationStyle.CASUAL_TYPING,
            language="en",
            turns=turns,
        )
        for _ in range(count)
    )
    return SyntheticDataset(
        run_id=uuid4(),
        seed=42,
        axes=axes,
        stage_mix=stage_mix,
        conversations=convs,
        generated_at=datetime.now(UTC),
        schema_version=1,
    )


def test_all_four_files_created(tmp_path: Path) -> None:
    dataset = _make_dataset()
    build_release_artifact(dataset, tmp_path)
    assert (tmp_path / "conversations.jsonl").exists()
    assert (tmp_path / "LICENSE").exists()
    assert (tmp_path / "DATASHEET.md").exists()
    assert (tmp_path / "manifest.json").exists()


def test_manifest_sha256_matches_jsonl(tmp_path: Path) -> None:
    dataset = _make_dataset()
    manifest = build_release_artifact(dataset, tmp_path)
    jsonl_bytes = (tmp_path / "conversations.jsonl").read_bytes()
    expected_sha = sha256(jsonl_bytes).hexdigest()
    assert manifest.sha256_conversations == expected_sha


def test_manifest_metadata_correct(tmp_path: Path) -> None:
    dataset = _make_dataset(5)
    manifest = build_release_artifact(dataset, tmp_path)
    assert manifest.conversation_count == 5
    assert manifest.seed == 42
    assert manifest.schema_version == 1
    assert manifest.version == "v1"


def test_jsonl_lines_equal_conversation_count(tmp_path: Path) -> None:
    dataset = _make_dataset(4)
    build_release_artifact(dataset, tmp_path)
    lines = (tmp_path / "conversations.jsonl").read_bytes().splitlines()
    assert len(lines) == 4


def test_jsonl_lines_are_valid_json(tmp_path: Path) -> None:
    dataset = _make_dataset(3)
    build_release_artifact(dataset, tmp_path)
    for line in (tmp_path / "conversations.jsonl").read_bytes().splitlines():
        obj = orjson.loads(line)
        assert "id" in obj
        assert "stage" in obj


def test_manifest_json_readable(tmp_path: Path) -> None:
    dataset = _make_dataset()
    build_release_artifact(dataset, tmp_path)
    manifest_data = orjson.loads((tmp_path / "manifest.json").read_bytes())
    assert manifest_data["version"] == "v1"
    assert "sha256_conversations" in manifest_data
