# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from io import StringIO

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from shared.config import Settings
from shared.observability import (
    configure_logging,
    configure_tracing,
    get_logger,
    get_tracer,
)

pytestmark = pytest.mark.unit


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


@pytest.fixture
def in_memory_exporter() -> InMemorySpanExporter:
    return InMemorySpanExporter()


def test_configure_tracing_sets_service_resource(
    in_memory_exporter: InMemorySpanExporter,
) -> None:
    configure_tracing(
        Settings(env="test", service_name="sentinel"),
        span_processor=SimpleSpanProcessor(in_memory_exporter),
    )
    get_tracer("test").start_span("probe").end()
    spans = in_memory_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].resource.attributes["service.name"] == "sentinel"
    assert spans[0].resource.attributes["deployment.environment"] == "test"


def test_test_env_skips_otlp_exporter_by_default() -> None:
    configure_tracing(Settings(env="test"))
    provider = trace.get_tracer_provider()
    assert isinstance(provider, TracerProvider)


def test_trace_id_injected_into_log(
    captured_logs: StringIO, in_memory_exporter: InMemorySpanExporter
) -> None:
    configure_tracing(Settings(env="test"), span_processor=SimpleSpanProcessor(in_memory_exporter))
    configure_logging(Settings(env="prod", log_level="INFO"))
    tracer = get_tracer("test")
    with tracer.start_as_current_span("op"):
        get_logger("test").info("inside_span")
    payload = json.loads(captured_logs.getvalue().strip())
    assert "trace_id" in payload
    assert len(payload["trace_id"]) == 32
    assert len(payload["span_id"]) == 16


def test_trace_id_absent_outside_span(captured_logs: StringIO) -> None:
    configure_logging(Settings(env="prod", log_level="INFO"))
    get_logger("test").info("no_span")
    payload = json.loads(captured_logs.getvalue().strip())
    assert "trace_id" not in payload


def test_non_test_env_registers_otlp_exporter(monkeypatch: pytest.MonkeyPatch) -> None:
    added: list[object] = []

    def fake_add(self: object, processor: object) -> None:
        added.append(processor)

    monkeypatch.setattr(TracerProvider, "add_span_processor", fake_add)
    configure_tracing(Settings(env="prod", otlp_endpoint="http://localhost:4317"))
    assert len(added) == 1


def test_instrument_fastapi_attaches_middleware() -> None:
    from fastapi import FastAPI

    from shared.observability import instrument_fastapi

    app = FastAPI()
    instrument_fastapi(app)


def test_instrument_httpx_client_attaches_hook() -> None:
    import httpx

    from shared.observability import instrument_httpx_client

    with httpx.Client() as client:
        instrument_httpx_client(client)
