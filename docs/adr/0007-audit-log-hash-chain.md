# ADR-0007: Audit log as SHA-256 hash chain with advisory-lock serialization

- Status: Accepted
- Date: 2026-04-01
- Deciders: Platform team, Compliance, Security

## Context

Section 11 requires append-only, tamper-evident audit logs. Section 10 lists multi-year retention for regulatory reasons (COPPA, GDPR, UK OSA). Investigators must be able to detect any row mutation after the fact.

Simultaneously, many services write to the audit log per tenant and the log must preserve a linear sequence: gap or reorder equals broken forensics.

## Decision

- Every audit entry stores `sequence` (monotonic per tenant starting at 1), `previous_entry_hash`, and `entry_hash = SHA-256(canonical_json(entry_without_hash))`.
- The genesis row's `previous_entry_hash` is 64 zero hex characters.
- Writes are serialized per tenant by `pg_advisory_xact_lock(hashtext('audit:' || tenant_id)::bigint)` inside the same transaction as the insert. Concurrent writers queue behind the lock rather than racing.
- `verify_chain(tenant_id)` walks entries in sequence order and raises `AuditChainBrokenError` for gaps or mismatched previous-hash, and `AuditTamperedError` for a row whose recomputed hash does not match the stored hash.
- Canonical JSON is produced by `orjson.dumps(..., option=OPT_SORT_KEYS)` with explicit coercions (`str(UUID)`, `datetime.isoformat()`) to keep the bytes stable across Python driver quirks.

## Alternatives considered

- **Merkle tree per day / per tenant** — rejected for Phase 0–3: overkill when linear chain already detects tampering; revisit when we need export-time proofs.
- **External notarization (timestamping service)** — deferred to Phase 9+; valuable but not a Phase 0 requirement.
- **Row version + trigger-based hashing in PostgreSQL** — rejected: couples logic to the DB and makes multi-store consistency harder later.

## Consequences

### Positive

- Any post-hoc mutation of an audit row is detectable in one pass.
- Sequence gaps surface bugs in writers immediately.
- Advisory locks are cheap and release with the transaction — no orphan locks.

### Negative / Trade-offs

- Write throughput per tenant is serialized. Tenants with extremely high event volume may need sharded audit streams (deferred).
- Chain verification is O(n) in entries; for large audit logs we will add range-bounded verification and pre-computed checkpoints in a later ADR.

### Neutral

- Hash algorithm is pluggable via `shared.audit.hashing`; a future ADR can rotate to SHA-3 without changing callers.
