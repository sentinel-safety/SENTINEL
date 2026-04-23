# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from hashlib import sha256
from typing import Protocol
from uuid import uuid4

from shared.contracts.preprocess import ExtractedFeatures
from shared.patterns import Pattern, PatternMatch, SyncPatternContext
from shared.schemas.base import FrozenModel
from shared.schemas.enums import EventType
from shared.schemas.event import Event
from shared.synthetic.axes import GroomingStage
from shared.synthetic.dataset import SyntheticConversation, SyntheticDataset


class ReferenceConversation(FrozenModel):
    id: object
    stage: GroomingStage
    turns: tuple[object, ...]
    label: bool = True


class RealDatasetAdapter(Protocol):
    def iter_conversations(self) -> Iterable[ReferenceConversation]: ...


class MockRealDatasetAdapter:
    def __init__(self, conversations: tuple[ReferenceConversation, ...]) -> None:
        self._conversations = conversations

    def iter_conversations(self) -> Iterable[ReferenceConversation]:
        return self._conversations


class DetectionMetrics(FrozenModel):
    precision: float
    recall: float
    f1: float
    per_stage_f1: dict[str, float]


class ValidationReport(FrozenModel):
    synthetic_metrics: DetectionMetrics
    real_metrics: DetectionMetrics
    deltas: dict[str, float]
    parity_achieved: bool


def _dummy_event() -> Event:
    return Event(
        id=uuid4(),
        tenant_id=uuid4(),
        conversation_id=uuid4(),
        actor_id=uuid4(),
        timestamp=datetime.now(UTC),
        type=EventType.MESSAGE,
        content_hash=sha256(b"x").hexdigest(),
    )


def _features_from_text(text: str) -> ExtractedFeatures:
    return ExtractedFeatures(
        normalized_content=text[:10_000],
        language="en",
        token_count=len(text.split()),
        contains_url="http" in text,
        contains_contact_request=False,
        minor_recipient=True,
        late_night_local=False,
    )


async def _score_text(text: str, patterns: Sequence[Pattern]) -> tuple[PatternMatch, ...]:
    ctx = SyncPatternContext(
        event=_dummy_event(),
        features=_features_from_text(text),
    )
    matches: list[PatternMatch] = []
    for p in patterns:
        matches.extend(await p.detect_sync(ctx))
    return tuple(matches)


def _metrics_for_scored(
    scored: list[tuple[bool, bool]],
    per_stage: dict[str, list[tuple[bool, bool]]],
) -> DetectionMetrics:
    tp = sum(1 for label, pred in scored if label and pred)
    fp = sum(1 for label, pred in scored if not label and pred)
    fn = sum(1 for label, pred in scored if label and not pred)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    stage_f1: dict[str, float] = {}
    for stage, pairs in per_stage.items():
        s_tp = sum(1 for lbl, pred in pairs if lbl and pred)
        s_fp = sum(1 for lbl, pred in pairs if not lbl and pred)
        s_fn = sum(1 for lbl, pred in pairs if lbl and not pred)
        s_prec = s_tp / (s_tp + s_fp) if (s_tp + s_fp) > 0 else 0.0
        s_rec = s_tp / (s_tp + s_fn) if (s_tp + s_fn) > 0 else 0.0
        stage_f1[stage] = 2 * s_prec * s_rec / (s_prec + s_rec) if (s_prec + s_rec) > 0 else 0.0
    return DetectionMetrics(precision=precision, recall=recall, f1=f1, per_stage_f1=stage_f1)


async def run_baseline_detector(
    conversations: Iterable[SyntheticConversation],
    patterns: Sequence[Pattern],
) -> DetectionMetrics:
    scored: list[tuple[bool, bool]] = []
    per_stage: dict[str, list[tuple[bool, bool]]] = {}

    for conv in conversations:
        stage_key = conv.stage.value
        full_text = " ".join(t.text for t in conv.turns)
        matches = await _score_text(full_text, patterns)
        predicted = len(matches) > 0
        per_stage.setdefault(stage_key, []).append((True, predicted))
        scored.append((True, predicted))

    return _metrics_for_scored(scored, per_stage)


async def run_baseline_detector_on_reference(
    conversations: Iterable[ReferenceConversation],
    patterns: Sequence[Pattern],
) -> DetectionMetrics:
    scored: list[tuple[bool, bool]] = []
    per_stage: dict[str, list[tuple[bool, bool]]] = {}

    for conv in conversations:
        stage_key = conv.stage.value
        texts = [t for t in conv.turns if isinstance(t, str)]
        full_text = " ".join(texts) if texts else ""
        matches = await _score_text(full_text, patterns)
        predicted = len(matches) > 0
        per_stage.setdefault(stage_key, []).append((conv.label, predicted))
        scored.append((conv.label, predicted))

    return _metrics_for_scored(scored, per_stage)


async def validate_against_baseline(
    synthetic: SyntheticDataset,
    real_adapter: RealDatasetAdapter,
    patterns: Sequence[Pattern],
) -> ValidationReport:
    synthetic_metrics = await run_baseline_detector(synthetic.conversations, patterns)
    real_metrics = await run_baseline_detector_on_reference(
        real_adapter.iter_conversations(), patterns
    )
    deltas: dict[str, float] = {
        "f1": abs(synthetic_metrics.f1 - real_metrics.f1),
    }
    for stage in set(synthetic_metrics.per_stage_f1) | set(real_metrics.per_stage_f1):
        s_f1 = synthetic_metrics.per_stage_f1.get(stage, 0.0)
        r_f1 = real_metrics.per_stage_f1.get(stage, 0.0)
        deltas[f"stage_{stage}"] = abs(s_f1 - r_f1)

    parity_achieved = all(v <= 0.05 for v in deltas.values())
    return ValidationReport(
        synthetic_metrics=synthetic_metrics,
        real_metrics=real_metrics,
        deltas=deltas,
        parity_achieved=parity_achieved,
    )
