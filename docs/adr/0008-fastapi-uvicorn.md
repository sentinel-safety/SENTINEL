# ADR-0008: FastAPI + uvicorn for HTTP services

- Status: Accepted
- Date: 2026-04-01
- Deciders: Platform team

## Context

Each SENTINEL service (gateway, ingestion, scoring, …) exposes an HTTP surface and/or consumes one from a sibling service. The spec demands p99 < 200 ms on the hot path and clean typed contracts with pydantic schemas.

The HTTP framework must:

- Be async-native so it pairs with async SQLAlchemy (ADR-0004).
- Integrate with Pydantic v2 models directly (ADR-0005).
- Auto-generate OpenAPI from route definitions so the spec stays in sync with code.
- Have a battle-tested OpenTelemetry integration (ADR-0006).

## Decision

- **Framework:** FastAPI. Each service exposes a `create_app(settings)` factory so the app object is never constructed at import time (tests and uvicorn both use the factory).
- **ASGI server:** uvicorn with `factory=True` so CLI entrypoints are a one-liner per service.
- **Common surface:** `shared.web.create_service_app(...)` wires health/ready/version routes, request-id middleware, observability, and FastAPI instrumentation. Service-specific routers are passed in.

## Alternatives considered

- **Starlette only** — rejected: we would re-implement Pydantic integration and OpenAPI generation.
- **Flask + async extensions** — rejected: async story is clunky; typing support is weaker.
- **Litestar** — rejected: smaller community, fewer OpenTelemetry integrations; revisit if FastAPI stalls.

## Consequences

### Positive

- OpenAPI for every service for free; the dashboard and downstream clients can generate typed SDKs.
- `shared.web` enforces the same healthcheck and correlation behavior in every service; we cannot "forget" to wire observability.
- Testing uses `TestClient` (sync wrapper) for simple assertions or `httpx.AsyncClient` for async cases — both work out of the box.

### Negative / Trade-offs

- FastAPI's dependency-injection magic can hide errors at startup. The factory pattern mitigates by making the wiring explicit.
- uvicorn with reload is dev-only; production will run behind a gunicorn/uvicorn workers setup (ADR to follow when we size infra).

### Neutral

- Middleware composition is stable; request-id middleware is Starlette-level and transfers to any ASGI framework if we ever migrate.
