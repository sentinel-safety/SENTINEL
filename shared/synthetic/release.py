# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from pathlib import Path

import orjson

from shared.schemas.base import FrozenModel
from shared.synthetic.dataset import SyntheticDataset

_LICENSE_TEXT = """\
Creative Commons Attribution 4.0 International (CC BY 4.0)
https://creativecommons.org/licenses/by/4.0/

USE RESTRICTION ADDENDUM
This dataset is released solely for safety research into child protection and
online-grooming detection. Any use that facilitates, promotes, or enables harm
to minors is strictly prohibited. By using this dataset you agree to these terms.
"""

_DATASHEET_TEMPLATE = """\
# Datasheet for SENTINEL Synthetic Grooming Dataset

## Motivation
Generated to support safety-research training and evaluation of grooming-detection models.

## Composition
- Conversations: {conversation_count}
- Schema version: {schema_version}
- Seed: {seed}
- Axes: {axes}
- Stage mix: {stage_mix}

## Collection Process
Synthetically generated; no real individuals involved.

## Preprocessing
Forbidden-token safety filtering applied during generation.

## Uses
Intended use: training and evaluation of grooming-detection classifiers.
Prohibited use: any application that harms or facilitates harm to minors.

## Distribution
CC BY 4.0 with use-restriction addendum (see LICENSE).

## Maintenance
Maintained by the SENTINEL project team.
"""


class ReleaseManifest(FrozenModel):
    sha256_conversations: str
    schema_version: int
    seed: int
    axes: dict[str, object]
    stage_mix: dict[str, object]
    conversation_count: int
    generated_at: datetime
    version: str = "v1"


def build_release_artifact(dataset: SyntheticDataset, out_dir: Path) -> ReleaseManifest:
    out_dir.mkdir(parents=True, exist_ok=True)

    jsonl_lines = b"\n".join(orjson.dumps(c.model_dump(mode="json")) for c in dataset.conversations)
    sha = sha256(jsonl_lines).hexdigest()

    (out_dir / "conversations.jsonl").write_bytes(jsonl_lines)
    (out_dir / "LICENSE").write_text(_LICENSE_TEXT, encoding="utf-8")
    (out_dir / "DATASHEET.md").write_text(
        _DATASHEET_TEMPLATE.format(
            conversation_count=len(dataset.conversations),
            schema_version=dataset.schema_version,
            seed=dataset.seed,
            axes=dataset.axes.model_dump(),
            stage_mix=dataset.stage_mix.model_dump(),
        ),
        encoding="utf-8",
    )

    manifest = ReleaseManifest(
        sha256_conversations=sha,
        schema_version=dataset.schema_version,
        seed=dataset.seed,
        axes=dataset.axes.model_dump(),
        stage_mix=dataset.stage_mix.model_dump(),
        conversation_count=len(dataset.conversations),
        generated_at=dataset.generated_at,
        version="v1",
    )
    (out_dir / "manifest.json").write_bytes(
        orjson.dumps(manifest.model_dump(mode="json"), option=orjson.OPT_INDENT_2)
    )
    return manifest
