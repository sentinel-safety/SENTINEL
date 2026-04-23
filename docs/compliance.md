# SENTINEL Compliance

Compliance is non-optional and built in from the first commit. Each regulation below has a dedicated module under `shared/compliance/` with types, enums, and retention defaults that the rest of the platform consumes.

> Nothing in this document constitutes legal advice. Tenants are responsible for filing reports, collecting consent, and signing DPAs with their own counsel.

## 1. Jurisdictions covered

| Jurisdiction | Module | Key regimes |
|---|---|---|
| US | `compliance/coppa`, `compliance/audit_log` | COPPA, NCMEC CyberTipline |
| EU | `compliance/gdpr`, `compliance/dsa` | GDPR, EU Digital Services Act |
| UK | `compliance/uk_osa` | UK Online Safety Act |

Tenants declare jurisdictions in tenant settings (see `shared.schemas.tenant.Tenant`). `compliance.jurisdictions.regimes_for_all(...)` returns the full list of regimes a tenant is subject to.

## 2. Retention

`compliance.retention_policies` defines defaults per jurisdiction:

| Jurisdiction | Events | Suspicion profile | Audit log | Raw content |
|---|---|---|---|---|
| US | 365 days | 730 days | 7 years | 90 days |
| EU | 180 days | 365 days | 7 years | 30 days |
| UK | 365 days | 730 days | 7 years | 90 days |

`strictest_policy(jurisdictions)` combines multiple jurisdictions into the most conservative envelope (shortest retention windows, longest audit log retention). Tenants can tighten but never loosen beyond these defaults.

## 3. COPPA (US, under-13)

Types in `compliance.coppa`:

- `ParentalConsentStatus` — `unknown | not_required | pending | granted | revoked`
- `ParentalConsentRecord` — immutable record with `granted_at`, `revoked_at`, `method`, and `evidence_reference`
- `COPPA_AGE_THRESHOLD = 13`, `COPPA_MAX_RETENTION_DAYS = 90`

The platform is responsible for verifiable parental consent flows. SENTINEL stores the outcome and gates behavioral profiling on `ParentalConsentRecord.is_effective_at(now)`.

## 4. GDPR (EU)

Types in `compliance.gdpr`:

- `LawfulBasis` — the six Article 6 bases
- `LawfulBasisDeclaration` — per-tenant, documented in writing, linked from the tenant's DPA
- `ErasureRequest` — Article 17 request lifecycle (`received | verified | in_progress | completed | rejected`)

Erasure is actor-scoped and exposed via `POST /dashboard/api/compliance/gdpr/erasure` (admin-only). Event rows and derived records are deleted; audit log entries are pseudonymised (Article 17 §3(b)) rather than removed, preserving the hash chain.

## 5. EU DSA

Types in `compliance.dsa`:

- `TransparencyReport` — moderation stats per reporting period (monthly / quarterly / annual)
- `TrustedFlaggerRegistration` — verified flaggers receive prioritized review

SENTINEL emits transparency-report inputs on demand; the tenant files the formal report with the European Commission.

## 6. UK Online Safety Act

Types in `compliance.uk_osa`:

- `HarmCategory` — CSEA, grooming, bullying, self-harm, hate
- `RiskLevel` — low / medium / high
- `RiskAssessment` — periodic risk assessment with mitigations and a next-review date

Tenants must commission their own formal risk assessment; SENTINEL deployment is evidence of proactive moderation.

## 7. US Mandatory Reporting (NCMEC)

When a US-jurisdiction tenant hits critical-tier grooming patterns, SENTINEL emits a `mandatory_report.required` event. SENTINEL does **not** file reports — that is the platform's legal obligation — but supplies the evidence package (raw events, pattern matches, timeline, actor graph).

## 8. Audit log

`compliance.audit_log`:

- `AUDIT_LOG_RETENTION_YEARS = 7`
- `AuditExportFormat` — `jsonl | csv`
- `AuditExportRequest` — an auditor-initiated export for a bounded time range

The underlying hash chain is implemented in `shared.audit` and documented in ADR-0007.

## 9. Federation

Cross-tenant threat signals are exchanged as non-invertible behavioural fingerprints with HMAC-pseudonymised actor identifiers. Full data-minimisation commitments, reputation model, dispute process, and MOU requirements: [`compliance/federation-governance.md`](compliance/federation-governance.md).

## 10. How it fits together

1. Tenant onboarding declares jurisdictions + lawful bases.
2. `shared.schemas.tenant.Tenant` stores jurisdictions as `frozenset[Jurisdiction]`.
3. Retention windows are resolved via `strictest_policy(...)` and cached per tenant.
4. Request-time checks consult `ParentalConsentRecord.is_effective_at(...)` for COPPA-affected actors.
5. Every score change, every moderator action, every erasure request lands in the audit log.
