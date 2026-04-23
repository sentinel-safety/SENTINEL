# ADR-0006: structlog + OpenTelemetry for logs and traces

- Status: Accepted
- Date: 2026-04-01
- Deciders: Platform team

## Context

Every service needs:

- JSON structured logs for indexing (tenant, actor, request_id).
- Distributed traces that follow an event through gateway → ingestion → scoring → response.
- Trace-to-log correlation so we can jump from a latency spike in a span to the exact log lines it produced.

Handlers must be test-friendly: fixtures swap renderers (JSON vs human) and capture lines without touching global state permanently.

## Decision

- **Logging:** `structlog` with `contextvars` for ambient bindings (`tenant_id`, `request_id`, `actor_id`). JSON renderer in prod/staging/test, ConsoleRenderer in dev. orjson serializer so UUIDs and datetimes serialize without custom hooks.
- **Tracing:** OpenTelemetry SDK with `OTLPSpanExporter` (gRPC) to a Jaeger all-in-one collector in dev and to the tenant's chosen APM in prod.
- **Correlation:** `_inject_trace_context` structlog processor reads the active span and adds `trace_id` and `span_id` to every log entry.
- **Instrumentation:** FastAPI and httpx are auto-instrumented via the OTel contrib packages.

## Alternatives considered

- **stdlib logging JSON formatter + OTel** — rejected: stdlib makes contextvar propagation clumsy; structlog's processor pipeline is cleaner.
- **Sentry-only** — rejected: no general log aggregation; tied to a single vendor.
- **Print statements during Phase 0** — non-starter; observability is a non-negotiable deliverable.

## Consequences

### Positive

- Single log and trace pipeline per service; same code in dev and prod.
- Contextvars bind once per request and auto-propagate to background tasks, so tenant and request IDs are never lost.
- Tests use a `StringIO` handler + `InMemorySpanExporter` — no mocks needed.

### Negative / Trade-offs

- Dev renderer differs from prod; tests must pin `env="prod"` when asserting JSON. The fixture makes this explicit.
- OTel SDK is heavy on startup. Mitigated by lazy imports of FastAPI/httpx instrumentation helpers.

### Neutral

- Any OTLP-compatible backend works without code changes.
