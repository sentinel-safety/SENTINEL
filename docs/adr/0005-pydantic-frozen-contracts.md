# ADR-0005: Pydantic v2 FrozenModel for all cross-boundary data

- Status: Accepted
- Date: 2026-04-01
- Deciders: Platform team

## Context

SENTINEL moves structured data across many boundaries: HTTP handlers ↔ services, services ↔ queues, services ↔ databases, database ↔ audit hash-chain. A single field drift (e.g., `score` becomes `suspicion_score`) between producers and consumers can silently corrupt downstream state.

The schemas must be:

- **Immutable** once constructed so they cannot be mutated mid-pipeline.
- **Strict** — reject unknown fields, reject naive datetimes, coerce nothing unless explicit.
- **Serializable** to stable JSON for logging, queue payloads, and audit-log hash input.
- **Typed** so mypy surfaces contract drift before tests.

## Decision

All cross-boundary data types subclass `shared.schemas.base.FrozenModel`:

- `model_config = ConfigDict(frozen=True, extra="forbid", strict=True, str_strip_whitespace=True)`
- Datetimes annotated with `UtcDatetime` — rejects naive timestamps and normalizes to UTC.
- Default JSON serializer is `orjson` with sorted keys.

Dataclasses are only used inside a single module for transient aggregates.

## Alternatives considered

- **attrs + cattrs** — rejected: less ecosystem for FastAPI, weaker runtime validation surface.
- **TypedDict / dataclasses** — rejected: no runtime validation, no built-in serialization.
- **Protobuf** — deferred to Phase 10 (federation) where wire compactness matters; in-process and HTTP traffic stays on JSON.

## Consequences

### Positive

- Any mutation attempt raises at runtime and is caught by unit tests.
- Unknown fields are rejected, so a typo in a queue consumer fails loudly instead of silently dropping data.
- Audit log hash input is stable because orjson + sorted keys produces deterministic bytes.

### Negative / Trade-offs

- Pydantic models cost more to construct than raw dicts. Acceptable given our latency envelope; profiling Phase 1 will confirm.
- Cannot mutate fields post-construction; callers must use `model_copy(update=...)`. Small ergonomic cost for huge correctness gain.

### Neutral

- Pydantic v2 is the dominant data-validation library; contributors need no training.
