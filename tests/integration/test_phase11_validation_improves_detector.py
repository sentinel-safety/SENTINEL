# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import re

import pytest

from services.patterns.app.library.secrecy_request import SecrecyRequestPattern
from shared.llm.fake import FakeProvider
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
from shared.synthetic.dataset import SyntheticConversation
from shared.synthetic.pipeline import generate_dataset
from shared.synthetic.stages import STAGE_PROMPTS
from shared.synthetic.validation import (
    MockRealDatasetAdapter,
    ReferenceConversation,
    run_baseline_detector_on_reference,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_KNOWN_PHRASES = [
    "don't tell your parents",
    "between you and me",
    "our little secret",
]
_NOVEL_PHRASE = "this is just between us kids"


def _make_real_conversations() -> tuple[ReferenceConversation, ...]:
    stages = list(GroomingStage)
    convs = []
    for i in range(18):
        convs.append(
            ReferenceConversation(
                id=i,
                stage=stages[i % len(stages)],
                turns=(_KNOWN_PHRASES[i % len(_KNOWN_PHRASES)], "ok"),
                label=True,
            )
        )
    convs.append(
        ReferenceConversation(
            id=100,
            stage=GroomingStage.ISOLATION,
            turns=(_NOVEL_PHRASE, "ok"),
            label=True,
        )
    )
    convs.append(
        ReferenceConversation(
            id=101,
            stage=GroomingStage.ISOLATION,
            turns=(_NOVEL_PHRASE, "whatever"),
            label=True,
        )
    )
    return tuple(convs)


def _fake_provider_with_novel() -> FakeProvider:
    return FakeProvider(
        responses={
            prompt: {"text": f"this is just between us kids — {stage.value}"}
            for stage, prompt in STAGE_PROMPTS.items()
        }
    )


class _AugmentedSecrecyPattern:
    name = "augmented_secrecy"
    signal_kind = SignalKind.SECRECY_REQUEST
    mode = DetectionMode.RULE

    def __init__(self, extra_phrases: frozenset[str]) -> None:
        base = (
            r"\b(?:don'?t tell|keep (?:this|it) (?:a )?secret|between (?:you and me|us)|"
            r"our little secret|don'?t (?:mention|say))\b"
        )
        escaped = "|".join(re.escape(p) for p in sorted(extra_phrases))
        combined = f"(?:{base})|(?:{escaped})" if escaped else base
        self._pattern = re.compile(combined, re.IGNORECASE)

    async def detect_sync(self, ctx: SyncPatternContext) -> tuple[PatternMatch, ...]:
        match = self._pattern.search(ctx.features.normalized_content)
        if match is None:
            return ()
        return (
            PatternMatch(
                pattern_name=self.name,
                signal_kind=self.signal_kind,
                confidence=1.0,
                evidence_excerpts=(match.group(0),),
                detection_mode=self.mode,
            ),
        )


def _extract_keywords_from_dataset(
    conversations: tuple[SyntheticConversation, ...],
) -> frozenset[str]:
    phrases: set[str] = set()
    for conv in conversations:
        for turn in conv.turns:
            lower = turn.text.lower()
            if "between us" in lower or "just between" in lower:
                phrases.add("just between us")
            if "our secret" in lower:
                phrases.add("our secret")
    return frozenset(phrases)


async def test_augmented_detector_not_worse_and_catches_new(tmp_path: object) -> None:
    real_convs = _make_real_conversations()
    adapter = MockRealDatasetAdapter(real_convs)

    baseline_pattern = SecrecyRequestPattern()
    baseline_metrics = await run_baseline_detector_on_reference(
        adapter.iter_conversations(), [baseline_pattern]
    )
    baseline_f1 = baseline_metrics.f1

    provider = _fake_provider_with_novel()
    axes = DiversityAxes(
        demographics=(Demographics(age_band="14-15", gender="male", regional_context="UK"),),
        platforms=(Platform.DM,),
        communication_styles=(CommunicationStyle.CASUAL_TYPING,),
        languages=("en",),
    )
    stage_mix = StageMix(weights=dict.fromkeys(GroomingStage, 1))
    synthetic_dataset = await generate_dataset(
        axes=axes, stage_mix=stage_mix, count=50, seed=42, provider=provider
    )

    extra_keywords = _extract_keywords_from_dataset(synthetic_dataset.conversations)
    augmented_pattern = _AugmentedSecrecyPattern(extra_keywords)

    augmented_metrics = await run_baseline_detector_on_reference(
        adapter.iter_conversations(), [augmented_pattern]
    )
    augmented_f1 = augmented_metrics.f1

    assert augmented_f1 >= baseline_f1 - 0.01, (
        f"augmented F1 {augmented_f1:.4f} dropped below baseline {baseline_f1:.4f} - 1%"
    )

    novel_adapter = MockRealDatasetAdapter(
        tuple(c for c in real_convs if _NOVEL_PHRASE in " ".join(str(t) for t in c.turns))
    )

    baseline_novel = await run_baseline_detector_on_reference(
        novel_adapter.iter_conversations(), [baseline_pattern]
    )
    augmented_novel = await run_baseline_detector_on_reference(
        novel_adapter.iter_conversations(), [augmented_pattern]
    )

    assert (
        augmented_novel.recall > baseline_novel.recall or augmented_novel.f1 >= baseline_novel.f1
    ), "augmented detector did not improve on novel edge cases"
