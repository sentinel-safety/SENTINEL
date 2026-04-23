# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from io import StringIO
from uuid import UUID

import pytest

from shared.config import Settings
from shared.observability import (
    bind_tenant_id,
    configure_logging,
    get_logger,
)

pytestmark = pytest.mark.unit

_TENANT = UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def captured_logs() -> Iterator[StringIO]:
    buffer = StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    root.handlers = [handler]
    yield buffer
    root.handlers = original_handlers


def test_json_renderer_outputs_valid_json(captured_logs: StringIO) -> None:
    configure_logging(Settings(env="prod", log_level="INFO"))
    get_logger("test").info("hello", extra_field="value")
    line = captured_logs.getvalue().strip()
    payload = json.loads(line)
    assert payload["event"] == "hello"
    assert payload["extra_field"] == "value"
    assert payload["level"] == "info"
    assert "timestamp" in payload


def test_contextvars_merged_into_log_output(captured_logs: StringIO) -> None:
    configure_logging(Settings(env="prod", log_level="INFO"))
    bind_tenant_id(_TENANT)
    get_logger("test").info("with_context")
    payload = json.loads(captured_logs.getvalue().strip())
    assert payload["tenant_id"] == str(_TENANT)


def test_log_level_filters_below_threshold(captured_logs: StringIO) -> None:
    configure_logging(Settings(env="prod", log_level="WARNING"))
    log = get_logger("test")
    log.info("suppressed")
    log.warning("emitted")
    lines = [line for line in captured_logs.getvalue().splitlines() if line]
    assert len(lines) == 1
    assert json.loads(lines[0])["event"] == "emitted"


def test_dev_renderer_is_human_readable(captured_logs: StringIO) -> None:
    configure_logging(Settings(env="dev", log_level="INFO"))
    get_logger("test").info("readable")
    out = captured_logs.getvalue()
    assert "readable" in out
    assert not out.strip().startswith("{")


def test_uuid_values_serialize_without_error(captured_logs: StringIO) -> None:
    configure_logging(Settings(env="prod", log_level="INFO"))
    get_logger("test").info("uuid_field", tenant_id=_TENANT)
    payload = json.loads(captured_logs.getvalue().strip())
    assert payload["tenant_id"] == str(_TENANT)


def test_root_handler_added_when_none_present() -> None:
    root = logging.getLogger()
    original = list(root.handlers)
    root.handlers = []
    try:
        configure_logging(Settings(env="prod", log_level="INFO"))
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0], logging.StreamHandler)
    finally:
        root.handlers = original
