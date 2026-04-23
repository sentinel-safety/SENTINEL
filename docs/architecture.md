# SENTINEL Architecture

System-level view. For individual design decisions see the [ADRs](adr/).

## 1. One-paragraph summary

SENTINEL is a behavioral intelligence layer for platforms that host minors. Integrated platforms send events (messages, session metadata, profile changes) over HTTP. SENTINEL returns per-actor suspicion scores, response tiers, and structured recommended actions. Behavior is tracked across sessions (memory), across relationships (graph), and against a versioned pattern library. Every score change is written to a tamper-evident audit log.

## 2. High-level request flow

```
[Client Platform]
      │  REST / SDK / webhook
      ▼
[Gateway]  ← authn, API key auth, rate limit, tenant binding
      │
      ▼
[Ingestion]  ← validate schema, dedupe, queue
      │
      ▼
[Preprocessing]  ← normalize, language, feature extraction
      │
      ▼
[First-Pass Classifier]  ← fast; clearly-safe short-circuits here
      │                       │ (safe) → audit + return low score
      │ (needs deeper look)
      ▼
[Scoring Engine]  ←→  [Memory]  ←→  [Graph]  ←→  [Patterns]
      │
      ▼
[Suspicion Aggregator]  ← compute delta, apply decay, persist profile
      │
      ▼
[Response Engine]  ← tier calc, recommended actions
      │
      ▼
[Explainability]  ← human-readable reasoning
      │
      ▼
[Return to client] + [Dashboard update] + [Audit log] + [Webhooks]
```

Async branches:

- **Federation:** anonymized fingerprints are published to subscribing tenants (see [`compliance/federation-governance.md`](compliance/federation-governance.md)).
- **Synthetic data:** standalone pipeline for training; not in the request path.

## 3. Services

| Service | Port (dev) | Role |
|---|---|---|
| gateway | 8000 | Auth, rate limit, tenant binding |
| ingestion | 8001 | Intake, validate, dedupe, queue |
| preprocessing | 8002 | Normalize text, language detection, feature extraction |
| classifier-first-pass | 8003 | Low-cost filter before the deep pipeline |
| scoring | 8004 | Suspicion aggregator, decay, profile persistence |
| memory | 8005 | Cross-session event and score history |
| graph | 8006 | Relationship edges and network-level queries |
| patterns | 8007 | Detector library (rule- and LLM-backed) |
| response | 8008 | Tier calculation, action recommendation |
| dashboard_bff | 8009 | Moderator dashboard backend-for-frontend |
| honeypot | 8010 | Decoy minor personas (default-off, five-gate activation) |
| federation | 8011 | Cross-tenant fingerprint exchange |
| synthetic-data | 8012 | Synthetic training-corpus generator |

Every service is a FastAPI app built by `shared.web.create_service_app(...)`. Health endpoints (`/healthz`, `/readyz`, `/version`) and request-id correlation are wired the same way everywhere.

## 4. Data stores

- **PostgreSQL 16 + Apache AGE** — rows, graph edges, audit log. Row-level security enforces tenant isolation (ADR-0003).
- **Redis 7** — rate limits, ephemeral queues, rolling counters.
- **Qdrant 1.12** — vector storage for embedding-based similarity (patterns, honeypot matching, federation fingerprints).

## 5. Cross-cutting concerns

- **Tenant isolation** — every DB session sets `app.tenant_id` via `shared.db.session.tenant_session()`; RLS policies enforce the guard at the engine.
- **Audit log** — append-only SHA-256 hash chain; per-tenant advisory-lock serialization (ADR-0007). Erasure requests pseudonymize entries (GDPR Article 17 §3(b)) rather than deleting them, preserving the chain.
- **Observability** — structlog JSON logs with OTel trace/span IDs injected; traces exported via OTLP to the tenant's APM (ADR-0006).
- **Configuration** — Pydantic `Settings` loaded from `SENTINEL_*` environment variables; the shared web factory binds `service_name` per service.
- **Contracts** — all cross-boundary payloads are `FrozenModel` subclasses with strict validation (ADR-0005).
