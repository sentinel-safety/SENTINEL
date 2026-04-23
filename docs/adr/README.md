# Architecture Decision Records

ADRs capture significant architectural decisions — the context, the choice, the alternatives, and the consequences. They are append-only and versioned by filename.

## Index

| # | Title | Status |
|---|---|---|
| [0000](0000-template.md) | Template | — |
| [0001](0001-python-uv-toolchain.md) | Python 3.12 + uv as the project toolchain | Accepted |
| [0002](0002-monorepo-layout.md) | Monorepo layout with /shared, /services, /compliance | Accepted |
| [0003](0003-postgres-age-rls.md) | PostgreSQL + Apache AGE + row-level security | Accepted |
| [0004](0004-async-sqlalchemy-asyncpg.md) | Async SQLAlchemy 2.0 with asyncpg | Accepted |
| [0005](0005-pydantic-frozen-contracts.md) | Pydantic v2 FrozenModel for all cross-boundary data | Accepted |
| [0006](0006-structlog-opentelemetry.md) | structlog + OpenTelemetry for logs and traces | Accepted |
| [0007](0007-audit-log-hash-chain.md) | Audit log as SHA-256 hash chain with advisory-lock serialization | Accepted |
| [0008](0008-fastapi-uvicorn.md) | FastAPI + uvicorn for HTTP services | Accepted |

## Process

1. Copy `0000-template.md` to `NNNN-short-title.md` and fill in the sections.
2. Keep the status as `Proposed` during review.
3. On merge, flip the status to `Accepted`.
4. To reverse a decision, write a new ADR, set the old one's status to `Superseded by ADR-NNNN`, and link forward.

Do not edit an accepted ADR; record the change in a new one.
