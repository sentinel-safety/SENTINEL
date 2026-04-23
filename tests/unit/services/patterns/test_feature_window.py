# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from services.patterns.app.repositories.feature_window import (
    WindowRow,
    aggregate_window_from_rows,
)

pytestmark = pytest.mark.unit


def _row(
    timestamp: datetime | None = None,
    target_actor_ids: list[str] | None = None,
    conversation_id: UUID | None = None,
    content_features: dict[str, Any] | None = None,
) -> WindowRow:
    return WindowRow(
        timestamp=timestamp or datetime.now(UTC),
        target_actor_ids=target_actor_ids if target_actor_ids is not None else [str(uuid4())],
        conversation_id=conversation_id or uuid4(),
        content_features=content_features
        if content_features is not None
        else {
            "minor_recipient": True,
            "late_night_local": False,
            "contains_url": False,
            "contains_contact_request": False,
            "normalized_content": "hi",
        },
    )


def test_aggregate_counts_messages_and_characters() -> None:
    rows = [
        _row(content_features={"minor_recipient": True, "normalized_content": "hello"}),
        _row(content_features={"minor_recipient": False, "normalized_content": "world!"}),
    ]
    w = aggregate_window_from_rows(rows, actor_id=uuid4(), now=datetime.now(UTC))
    assert w.total_messages == 2.0
    assert w.minor_recipient_count == 1.0
    assert w.total_chars == 11.0


def test_aggregate_counts_distinct_conversations_and_targets() -> None:
    conv = uuid4()
    target = uuid4()
    rows = [
        _row(conversation_id=conv, target_actor_ids=[str(target)]),
        _row(conversation_id=conv, target_actor_ids=[str(target)]),
        _row(conversation_id=uuid4(), target_actor_ids=[str(uuid4())]),
    ]
    w = aggregate_window_from_rows(rows, actor_id=uuid4(), now=datetime.now(UTC))
    assert w.distinct_conversations == 2.0
    assert w.distinct_minor_targets == 2.0


def test_late_night_and_secrecy_and_platform_mentions() -> None:
    rows = [
        _row(
            content_features={
                "minor_recipient": True,
                "late_night_local": True,
                "normalized_content": "dont tell your parents",
            }
        ),
        _row(
            content_features={
                "minor_recipient": True,
                "normalized_content": "lets move to telegram",
            }
        ),
    ]
    w = aggregate_window_from_rows(rows, actor_id=uuid4(), now=datetime.now(UTC))
    assert w.late_night_count == 1.0
    assert w.secrecy_mentions == 1.0
    assert w.platform_migration_mentions == 1.0


def test_empty_input_returns_zero_window() -> None:
    w = aggregate_window_from_rows([], actor_id=uuid4(), now=datetime.now(UTC))
    assert w.total_messages == 0.0
    assert w.total_chars == 0.0
