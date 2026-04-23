# ADR-0003: PostgreSQL + Apache AGE + row-level security

- Status: Accepted
- Date: 2026-04-01
- Deciders: Platform team, Security

## Context

SENTINEL persists per-tenant behavioral data (actors, events, suspicion profiles) and relationship graphs (Phase 4+). Section 11 requires strict tenant isolation enforced at the database layer — an application-layer bug must not leak one customer's data to another. Section 4 also calls for graph queries over the relationship graph.

## Decision

- **Primary store:** PostgreSQL 16.
- **Graph extension:** Apache AGE (openCypher over PostgreSQL) using the `apache/age:release_PG16_*` Docker image in dev and CI.
- **Tenant isolation:** PostgreSQL row-level security (RLS) with `app.tenant_id` session GUC, enforced on every tenant-scoped table. Application connects as a restricted role (`sentinel_app`); only the migration role bypasses RLS.

## Alternatives considered

- **Separate graph database (Neo4j)** — rejected: doubles operational load, makes transactions across edges + rows impossible, complicates tenancy.
- **Schema-per-tenant** — rejected: thousands of schemas degrade pg_catalog performance and complicate migrations.
- **Application-layer tenant filters only** — rejected: one missing `WHERE tenant_id = ...` equals a data breach; RLS enforces it at the engine.

## Consequences

### Positive

- One transactional store for rows and graph queries.
- RLS makes accidental cross-tenant reads impossible by construction.
- Backups, PITR, and extensions benefit from PostgreSQL maturity.

### Negative / Trade-offs

- AGE is less widely deployed than Neo4j; we pin a specific image and have an exit strategy (ADR-0003a will cover migration path if AGE stalls).
- RLS requires every write to bind `app.tenant_id`; the helper `tenant_session()` centralizes this and is covered by integration tests.

### Neutral

- Graph queries that would be trivial in Cypher remain trivial; AGE exposes Cypher over SQL.
