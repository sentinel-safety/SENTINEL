# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Protocol, runtime_checkable

from shared.contracts.preprocess import ExtractedFeatures
from shared.fingerprint.repository import FingerprintNeighbor
from shared.graph.views import ContactGraphView
from shared.memory import ActorMemoryView
from shared.patterns.matches import DetectionMode, PatternMatch
from shared.schemas.base import FrozenModel
from shared.schemas.event import Event
from shared.scoring.signals import SignalKind


class SyncPatternContext(FrozenModel):
    event: Event
    features: ExtractedFeatures
    recent_distinct_minor_target_count: int = 0
    actor_memory: ActorMemoryView | None = None
    contact_graph: ContactGraphView | None = None
    fingerprint_neighbors: tuple[FingerprintNeighbor, ...] = ()


class LLMPatternContext(FrozenModel):
    event: Event
    features: ExtractedFeatures
    recent_messages: tuple[str, ...] = ()


@runtime_checkable
class Pattern(Protocol):
    name: str
    signal_kind: SignalKind
    mode: DetectionMode

    async def detect_sync(self, ctx: SyncPatternContext) -> tuple[PatternMatch, ...]: ...


@runtime_checkable
class LLMPattern(Protocol):
    name: str
    signal_kind: SignalKind
    mode: DetectionMode

    async def detect_llm(self, ctx: LLMPatternContext) -> tuple[PatternMatch, ...]: ...
