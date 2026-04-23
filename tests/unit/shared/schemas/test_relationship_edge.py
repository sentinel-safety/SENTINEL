# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from shared.schemas import RelationshipEdge

pytestmark = pytest.mark.unit


def _ordered_pair() -> tuple[UUID, UUID]:
    a, b = uuid4(), uuid4()
    return (a, b) if bytes(a.bytes) <= bytes(b.bytes) else (b, a)


def test_edge_rejects_self_loop() -> None:
    same = uuid4()
    now = datetime.now(UTC)
    with pytest.raises(ValidationError, match="self-loop"):
        RelationshipEdge(
            tenant_id=uuid4(),
            actor_a=same,
            actor_b=same,
            interaction_count=1,
            first_interaction=now,
            last_interaction=now,
        )


def test_edge_rejects_reversed_pair() -> None:
    a, b = _ordered_pair()
    now = datetime.now(UTC)
    with pytest.raises(ValidationError, match="smaller UUID"):
        RelationshipEdge(
            tenant_id=uuid4(),
            actor_a=b,
            actor_b=a,
            interaction_count=1,
            first_interaction=now,
            last_interaction=now,
        )


def test_edge_last_cannot_precede_first() -> None:
    a, b = _ordered_pair()
    now = datetime.now(UTC)
    with pytest.raises(ValidationError, match="precede"):
        RelationshipEdge(
            tenant_id=uuid4(),
            actor_a=a,
            actor_b=b,
            interaction_count=1,
            first_interaction=now,
            last_interaction=now - timedelta(minutes=1),
        )


def test_edge_happy_path_with_signals() -> None:
    a, b = _ordered_pair()
    now = datetime.now(UTC)
    e = RelationshipEdge(
        tenant_id=uuid4(),
        actor_a=a,
        actor_b=b,
        interaction_count=7,
        first_interaction=now - timedelta(days=2),
        last_interaction=now,
        signals={"age_gap_warning": True, "avg_message_gap_seconds": 32},
    )
    assert e.signals["age_gap_warning"] is True
    assert RelationshipEdge.model_validate(e.model_dump(mode="json")) == e
