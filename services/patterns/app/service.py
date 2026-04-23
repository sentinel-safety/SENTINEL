# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from shared.contracts.patterns import DetectRequest, DetectResponse
from shared.fingerprint.repository import FingerprintNeighbor
from shared.graph.views import ContactGraphView
from shared.memory import ActorMemoryView
from shared.patterns import Pattern, PatternMatch, SyncPatternContext


async def run_sync_patterns(
    request: DetectRequest,
    patterns: tuple[Pattern, ...],
    *,
    recent_distinct_minor_target_count: int = 0,
    actor_memory: ActorMemoryView | None = None,
    contact_graph: ContactGraphView | None = None,
    fingerprint_neighbors: tuple[FingerprintNeighbor, ...] = (),
) -> DetectResponse:
    ctx = SyncPatternContext(
        event=request.event,
        features=request.features,
        recent_distinct_minor_target_count=recent_distinct_minor_target_count,
        actor_memory=actor_memory,
        contact_graph=contact_graph,
        fingerprint_neighbors=fingerprint_neighbors,
    )
    all_matches: list[PatternMatch] = []
    for pattern in patterns:
        matches = await pattern.detect_sync(ctx)
        all_matches.extend(matches)
    return DetectResponse(matches=tuple(all_matches))
