# ADR-0004: Async SQLAlchemy 2.0 with asyncpg

- Status: Accepted
- Date: 2026-04-01
- Deciders: Platform team

## Context

SENTINEL services are HTTP-first (FastAPI) and event-driven (Redis streams, background workers). To keep p99 latency < 200 ms under realistic fan-out, I/O-bound code must not block the event loop. We need an ORM that:

- Speaks async natively to PostgreSQL.
- Lets us express complex tenant-scoped queries with typed constructs.
- Plays well with Alembic migrations and row-level security session GUCs.

## Decision

- **ORM:** SQLAlchemy 2.0 (typed, Mapped[] style) in async mode.
- **Driver:** `asyncpg` for application sessions; `psycopg[binary]` for Alembic migrations (sync) and advisory-lock-friendly maintenance tasks.
- **Session factory:** `shared/db/session.py` exposes `tenant_session(tenant_id)` which opens a connection, sets `app.tenant_id`, and returns an `AsyncSession`.

## Alternatives considered

- **Tortoise ORM / SQLModel** — rejected: weaker mypy coverage, smaller surface for complex queries, thinner extension support.
- **Raw asyncpg with hand-written SQL** — rejected: loses type safety; each service would re-invent query builders.
- **Synchronous SQLAlchemy + gunicorn threads** — rejected: higher memory per request, harder to compose with async HTTP clients.

## Consequences

### Positive

- Unified typed ORM across services; joins and subqueries stay readable.
- Async sessions integrate cleanly with FastAPI dependencies and structlog context.
- Alembic uses the same metadata; schema drift caught at migration time.

### Negative / Trade-offs

- Two drivers (asyncpg + psycopg) add a small dependency footprint. Necessary because Alembic's synchronous command API does not run under asyncpg cleanly.
- Async bugs (forgotten `await`, leaked sessions) are still possible; integration tests exercise session lifecycles.

### Neutral

- Future migration to PgBouncer is straightforward: asyncpg + session-mode pooling works out of the box.
