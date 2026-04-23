# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.patterns import DetectionMode, PatternMatch, SyncPatternContext
from shared.scoring.signals import SignalKind
from shared.synthetic.axes import (
    CommunicationStyle,
    Demographics,
    DiversityAxes,
    GroomingStage,
    Platform,
    StageMix,
)
from shared.synthetic.dataset import SyntheticConversation, SyntheticDataset, SyntheticTurn
from shared.synthetic.validation import (
    MockRealDatasetAdapter,
    ReferenceConversation,
    run_baseline_detector,
    validate_against_baseline,
)

pytestmark = pytest.mark.unit


class _AlwaysMatchPattern:
    name = "always_match"
    signal_kind = SignalKind.SECRECY_REQUEST
    mode = DetectionMode.RULE

    async def detect_sync(self, ctx: SyncPatternContext) -> tuple[PatternMatch, ...]:
        return (
            PatternMatch(
                pattern_name=self.name,
                signal_kind=self.signal_kind,
                confidence=1.0,
                evidence_excerpts=("matched",),
                detection_mode=self.mode,
            ),
        )


class _NeverMatchPattern:
    name = "never_match"
    signal_kind = SignalKind.SECRECY_REQUEST
    mode = DetectionMode.RULE

    async def detect_sync(self, ctx: SyncPatternContext) -> tuple[PatternMatch, ...]:
        return ()


def _make_dataset(count: int = 5) -> SyntheticDataset:
    from datetime import UTC, datetime
    from uuid import uuid4

    axes = DiversityAxes(
        demographics=(Demographics(age_band="14-15", gender="male", regional_context="UK"),),
        platforms=(Platform.DM,),
        communication_styles=(CommunicationStyle.CASUAL_TYPING,),
        languages=("en",),
    )
    stage_mix = StageMix(weights={GroomingStage.ISOLATION: 1})
    turns = (
        SyntheticTurn(role="actor", text="don't tell your parents", timestamp_offset_seconds=0),
        SyntheticTurn(role="target", text="ok", timestamp_offset_seconds=10),
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


def _make_ref_conversations(count: int = 5) -> tuple[ReferenceConversation, ...]:
    from uuid import uuid4

    return tuple(
        ReferenceConversation(
            id=uuid4(),
            stage=GroomingStage.ISOLATION,
            turns=("don't tell your parents", "ok"),
            label=True,
        )
        for _ in range(count)
    )


async def test_run_baseline_detector_always_match() -> None:
    dataset = _make_dataset(5)
    metrics = await run_baseline_detector(dataset.conversations, [_AlwaysMatchPattern()])
    assert metrics.f1 == 1.0
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0


async def test_run_baseline_detector_never_match() -> None:
    dataset = _make_dataset(5)
    metrics = await run_baseline_detector(dataset.conversations, [_NeverMatchPattern()])
    assert metrics.f1 == 0.0
    assert metrics.recall == 0.0


async def test_parity_achieved_when_both_match() -> None:
    dataset = _make_dataset(10)
    ref_convs = _make_ref_conversations(10)
    adapter = MockRealDatasetAdapter(ref_convs)
    report = await validate_against_baseline(dataset, adapter, [_AlwaysMatchPattern()])
    assert report.parity_achieved is True
    assert abs(report.deltas["f1"]) <= 0.05


async def test_parity_not_achieved_when_far_apart() -> None:
    dataset = _make_dataset(10)
    ref_convs = _make_ref_conversations(10)
    adapter = MockRealDatasetAdapter(ref_convs)
    report = await validate_against_baseline(dataset, adapter, [_NeverMatchPattern()])
    assert report.synthetic_metrics.f1 == report.real_metrics.f1 == 0.0
    assert report.parity_achieved is True


async def test_mock_adapter_iterates_all_conversations() -> None:
    ref_convs = _make_ref_conversations(7)
    adapter = MockRealDatasetAdapter(ref_convs)
    assert list(adapter.iter_conversations()) == list(ref_convs)
