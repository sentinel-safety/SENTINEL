# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from shared.schemas.base import FrozenModel
from shared.synthetic.axes import (
    CommunicationStyle,
    Demographics,
    DiversityAxes,
    GroomingStage,
    Platform,
    StageMix,
)


class SyntheticTurn(FrozenModel):
    role: Literal["actor", "target"]
    text: Annotated[str, Field(max_length=2000)]
    timestamp_offset_seconds: int


class SyntheticConversation(FrozenModel):
    id: UUID
    stage: GroomingStage
    demographics: Demographics
    platform: Platform
    communication_style: CommunicationStyle
    language: str
    turns: Annotated[tuple[SyntheticTurn, ...], Field(min_length=2)]


class SyntheticDataset(FrozenModel):
    run_id: UUID
    seed: int
    axes: DiversityAxes
    stage_mix: StageMix
    conversations: Annotated[tuple[SyntheticConversation, ...], Field(min_length=1)]
    generated_at: datetime
    schema_version: Literal[1] = 1
