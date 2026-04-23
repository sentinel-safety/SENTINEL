# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime
from uuid import UUID

from shared.explainability.context_summary import build_context_summary
from shared.explainability.next_review import compute_next_review_at
from shared.explainability.primary_drivers import rank_primary_drivers
from shared.graph.views import ContactGraphView
from shared.memory.repository import ActorMemoryView
from shared.patterns.matches import PatternMatch
from shared.schemas.enums import ResponseTier
from shared.schemas.reasoning import Reasoning


def _summarise_actions(action_kinds: tuple[str, ...]) -> str:
    if not action_kinds:
        return ""
    return "Recommended actions: " + ", ".join(action_kinds) + "."


def generate_reasoning(
    *,
    actor_id: UUID,
    tenant_id: UUID,
    previous_score: int,
    new_score: int,
    new_tier: ResponseTier,
    matches: tuple[PatternMatch, ...],
    contact_graph: ContactGraphView | None,
    actor_memory: ActorMemoryView | None,
    actor_age_days: int | None,
    action_kinds: tuple[str, ...],
    generated_at: datetime,
) -> Reasoning:
    return Reasoning(
        actor_id=actor_id,
        tenant_id=tenant_id,
        score_change=new_score - previous_score,
        new_score=new_score,
        new_tier=new_tier,
        primary_drivers=rank_primary_drivers(matches),
        context=build_context_summary(
            memory=actor_memory,
            contact_graph=contact_graph,
            actor_age_days=actor_age_days,
        ),
        recommended_action_summary=_summarise_actions(action_kinds),
        generated_at=generated_at,
        next_review_at=compute_next_review_at(new_tier, now=generated_at),
    )
