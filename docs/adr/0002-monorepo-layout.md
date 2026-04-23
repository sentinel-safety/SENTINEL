# ADR-0002: Monorepo layout with /shared, /services, /compliance

- Status: Accepted
- Date: 2026-04-01
- Deciders: Platform team

## Context

The specification (Section 3.3) mandates a single repository with strict module boundaries. Services must communicate only via defined event types, explicit API contracts, or shared utilities; never by reaching into another service's internals.

We need a directory layout that:

- Makes ownership obvious.
- Keeps cross-service types visible to reviewers so contract drift is noticed immediately.
- Allows a service to be lifted into its own container without repository surgery.

## Decision

Top-level layout:

```
/shared        domain schemas, events, db, errors, audit, observability, web factory
/services      one directory per bounded service, each with /app and Dockerfile
/compliance    COPPA, GDPR, DSA, UK OSA, retention policies, audit-log export
/infra         docker, k8s, terraform
/migrations    alembic
/tests         unit, integration, load, adversarial
/docs          adr, reference docs
```

Services may only depend on `/shared` and `/compliance`. Service-to-service imports are forbidden and enforced by review.

## Alternatives considered

- **Polyrepo** — rejected: cross-cutting schema changes would require synchronized releases across many repos.
- **`src/` layout per service with isolated venvs** — rejected: duplicates the dependency graph; breaks shared-schema import.
- **Layered monolith (e.g. Django project)** — rejected: would couple services at runtime, violating Section 3.4 (module boundary rules).

## Consequences

### Positive

- A reviewer can see every service surface in one place.
- Shared schemas prevent contract drift at compile time (mypy catches it before tests run).
- Tooling (pre-commit, CI, coverage) runs once for the whole platform.

### Negative / Trade-offs

- Any dependency bump touches every service; CI must run the whole suite. Acceptable at current scale.
- Requires discipline to keep `/shared` free of business logic — reinforced by a code-review checklist.

### Neutral

- Docker images copy only the files they need (`COPY shared`, `COPY services/<name>`) so image size is not inflated by the monorepo.
