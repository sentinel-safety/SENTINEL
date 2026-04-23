# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from shared.graph.views import ContactGraphView
from shared.memory.repository import ActorMemoryView


def build_context_summary(
    *,
    memory: ActorMemoryView | None,
    contact_graph: ContactGraphView | None,
    actor_age_days: int | None,
) -> str:
    parts: list[str] = []
    if contact_graph is not None and contact_graph.distinct_minor_contacts_window > 0:
        parts.append(
            f"Actor has interacted with "
            f"{contact_graph.distinct_minor_contacts_window} distinct minor accounts "
            f"in past {contact_graph.lookback_days} days."
        )
    if memory is not None and memory.distinct_minor_targets_last_window > 0:
        parts.append(
            f"Recent memory shows "
            f"{memory.distinct_minor_targets_last_window} distinct minor targets across "
            f"{memory.distinct_conversations_last_window} conversations."
        )
    if actor_age_days is not None:
        parts.append(f"Account was created {actor_age_days} days ago.")
    return " ".join(parts)
