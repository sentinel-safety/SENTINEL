# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Tracer

from shared.config import Settings

_configured: bool = False


def configure_tracing(settings: Settings, *, span_processor: SpanProcessor | None = None) -> None:
    global _configured

    resource = Resource.create(
        {
            "service.name": settings.service_name,
            "service.version": "0.0.1",
            "deployment.environment": settings.env,
        }
    )
    provider = TracerProvider(resource=resource)
    if span_processor is not None:
        provider.add_span_processor(span_processor)
    elif settings.env != "test":
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otlp_endpoint, insecure=True))
        )
    trace.set_tracer_provider(provider)
    _configured = True


def get_tracer(name: str) -> Tracer:
    return trace.get_tracer(name)


def instrument_fastapi(app: Any) -> None:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app)


def instrument_httpx_client(client: Any) -> None:
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

    HTTPXClientInstrumentor().instrument_client(client)


def reset_tracing() -> None:
    global _configured
    trace._TRACER_PROVIDER = None
    trace._TRACER_PROVIDER_SET_ONCE._done = False
    _configured = False
