# SENTINEL

Open-source behavioral intelligence for child safety moderation that detects grooming, exploitation, and coordinated targeting of minors from conversation patterns, relationship graphs, and temporal behavior, rather than simply relying on keyword filters. This effectively identifies slow-burn abuse. SENTINEL is a microservice backend that processes events sent over HTTP by platforms. It generates a per-actor risk score, a tier (`trusted` → `critical`), and structured reasoning for each decision. Every decision is logged in a cryptographically chained audit trail. Bias gates block model promotion on demographic parity breaches.

---

## For developers

Send an event and read back a score. `Authorization: Bearer sk_...` against a tenant-scoped API key.

```python
from sentinel import SentinelClient

client = SentinelClient(api_key="sk_...", base_url="https://api.example.com")
result = client.events.message(
    tenant_id="00000000-0000-0000-0000-000000000001",
    conversation_id="00000000-0000-0000-0000-000000000002",
    actor_external_id_hash="a" * 64,
    content="hey, you seem mature for your age",
)
print(result.tier, result.current_score)
```

Full SDK reference and webhook / idempotency / fail-open semantics: [`docs/sdk-docs/`](docs/sdk-docs/). Source: [`sdk/python/`](sdk/python/), [`sdk/node/`](sdk/node/).

## For operators

FastAPI services over PostgreSQL 16 (with Apache AGE + row-level security), Qdrant, and Redis. Local bring-up:

```bash
docker compose up -d
uv sync
uv run alembic upgrade head
uv run uvicorn services.ingestion.app.main:app --port 8001
```

Compliance surface: GDPR Article 17 erasure endpoint, 7-year hash-chained audit log, jurisdiction-aware retention (COPPA / GDPR / UK OSA), HMAC-SHA256 signed webhooks, mandatory FPR/FNR parity gates before any model promotion. System overview: [`docs/architecture.md`](docs/architecture.md). Compliance details: [`docs/compliance.md`](docs/compliance.md). Design decisions: [`docs/adr/`](docs/adr/).

## For researchers

The scoring engine composes four signal sources:

1. **Linguistic patterns** — 13 detectors covering grooming stages (LLM-backed) and rule-based markers (secrecy requests, platform migration, personal-info probes, gift offering).
2. **Contact graph** — Apache AGE tracks multi-party outreach; detects cross-conversation escalation, cluster membership, and behavioral-fingerprint similarity.
3. **Temporal dynamics** — linear decay on the suspicion score, suspended on qualifying cross-session escalation.
4. **Fairness gates** — FPR/FNR parity audits with a <10% demographic spread threshold required before any model ships.

Detectors, deltas, and calibration fixtures: [`services/patterns/`](services/patterns/). Synthetic research dataset (CC-BY-4.0 with use-restriction addendum): [`datasets/synthetic/`](datasets/synthetic/).

---

## License

Released under the **SENTINEL License Agreement** (see [`LICENSE`](LICENSE)):

Automatically converts to the **Apache License 2.0 on April 23, 2046** (twenty years from release), at which point all commercial and hosted-service restrictions terminate.
Governed by the laws of the Federal Republic of Germany.

Commercial licensing inquiries: `sentinel.childsafety@gmail.com`.

---

SENTINEL is v1.0 software. It is not yet a proper substitute for human moderator review, legal counsel, or mandatory reporting obligations. Operators are responsible for maintaining human oversight, managing consent flows, and complying with applicable law (COPPA, GDPR, UK OSA, CIPA, and others). SENTINEL does not file reports directly. Filing is the operator's legal obligation.
