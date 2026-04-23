# Federation Governance Document

**Version:** 1.0
**Effective date:** 2026-04-22
**Review cadence:** Annual
**Status:** Active

---

## 1. Purpose

SENTINEL's federation network allows independent platform operators ("tenants") to share
privacy-preserving threat signals about behavioural fingerprints associated with confirmed predatory
actors. The goal is to close the gap that exists when a bad actor is banned from one platform and
immediately resurfaces on another.

Federation is built on two foundational commitments:

**Protection of minors.** A predator who has been independently confirmed on Platform A should not
be able to operate undetected on Platform B simply because Platform B has not yet accumulated enough
signal to flag them. The network compresses that detection window from weeks or months to minutes,
without any platform disclosing identifying information about their users.

**Protection of the innocent.** Incorrect or malicious signals must be costly to the originator,
traceable to their source, and reversible by a defined dispute process. The system must never become
a mechanism for harassment, competitive sabotage, or mass false-flagging.

This document is the authoritative governance reference for all participating tenants. Admission to
the federation requires a signed Memorandum of Understanding (MOU) that explicitly references this
document by URL and version number. No tenant may participate without accepting these terms.

---

## 2. Data Minimization Commitments

### 2.1 What is shared

Every signal exchanged over the federation stream contains exactly the following fields and no
others:

| Field | Type | Purpose |
|---|---|---|
| `fingerprint` | 16-dimensional float vector | Behavioural fingerprint derived from the actor's interaction pattern. Never invertible to raw conversation content. |
| `actor_hash` | HMAC-SHA256 bytes | Pseudonymous actor identifier. Keyed with the publishing tenant's HMAC secret and actor pepper. Cannot be cross-correlated to another tenant's actor namespace without both secrets. |
| `signal_kinds` | list of strings | Pattern identifiers that contributed to the flag (e.g. `secrecy_request`, `sexual_escalation`). No message content. |
| `flagged_at` | ISO-8601 timestamp (UTC) | When the actor was elevated to the publishing threshold. |
| `publisher_tenant_id` | UUID | Identifies the publishing tenant for attribution, dispute routing, and reputation tracking. |
| `commit` | HMAC-SHA256 bytes | Cryptographic binding over the other fields, signed with the publisher's secret. Allows receivers to verify authenticity and integrity. |

The `schema_version` field (currently `1`) is also present to allow future format evolution without
breaking existing receivers.

### 2.2 What is never shared

The following categories of data are prohibited from appearing in any field of any federation
message. This prohibition is enforced at the protocol layer: signals are constructed from the
`FederationSignal` schema which contains no fields capable of holding this data.

- **Raw actor identifiers.** No platform user IDs, usernames, email addresses, phone numbers, or
  any other identifier that could be used to look up an account on the publishing platform.
- **Message content.** No text, images, audio, video, or metadata derived from the content of any
  conversation.
- **Conversation identifiers.** No conversation IDs, thread IDs, channel IDs, or session tokens.
- **Platform identifiers.** No information about which platform or application generated the signal.
- **Demographic data.** No age, gender, ethnicity, nationality, or other personal characteristics
  of the flagged actor or any conversation participant.
- **Victim information.** No information about any target of the flagged actor's behaviour.
- **IP addresses or device identifiers.** No network identifiers of any kind.

Receiving tenants MUST NOT attempt to infer any of the above from the fields that are shared. Any
such inference attempt constitutes a breach of the MOU and grounds for immediate revocation.

### 2.3 Audit trail

Every signal received by a tenant is written to `audit_log_entry` with `event_kind=federation_received`.
Every match against a federated signal is written with `event_kind=federation_match`. These records
preserve the full signal envelope but confirm the absence of raw actor IDs. The audit sweep in the
acceptance test suite (`tests/integration/test_phase10_federation_match.py`) verifies this
invariant automatically on every CI run.

---

## 3. Opt-In Mechanics

### 3.1 Tenant-level feature flags

Federation is disabled by default at the platform level (`federation_enabled_globally=false`) and at
the tenant level. A tenant participates only after setting all of the following flags to `true` in
their tenant configuration:

- `federation_publish_enabled` — allows this tenant to publish signals to the stream.
- `federation_subscribe_enabled` — allows this tenant to receive and act on signals from others.

Setting `federation_subscribe_enabled` without `federation_publish_enabled` is permitted. A tenant
may choose to receive signals (benefiting from the network's collective intelligence) without
contributing their own. This asymmetric participation is tracked in the reputation system; purely
subscribing tenants accrue no reputation but also incur no risk of false-signal penalties.

### 3.2 Acknowledgment gate

Before either flag can be set to `true`, the tenant admin must set
`federation_governance_acknowledged=true`. This field can only be set via the admin API endpoint
`POST /internal/admin/tenants/{id}/federation-acknowledge`, which logs the action to
`audit_log_entry`. The acknowledgment records the admin's user ID, the timestamp, and the version
of this document they accepted. Downgrading `federation_governance_acknowledged` to `false` after
enabling participation is treated as an immediate kill-switch (see §3.4).

### 3.3 Granular publish/subscribe/jurisdiction filters

Publishing tenants may configure:

- **`federation_publish_tier_threshold`** — minimum actor tier required to publish a signal.
  Default is `restrict` (tier 4). Lowering this threshold increases signal volume and false-positive
  risk; raising it reduces coverage.
- **`federation_jurisdictions`** — list of jurisdiction codes. Signals are only published for actors
  whose inferred jurisdiction matches. Receiving tenants may also filter incoming signals by
  jurisdiction. An empty list means no jurisdiction filter (all signals published/received).

Subscriber tenants may additionally configure:

- **`federation_subscriber_reputation_floor`** — minimum publisher reputation score (0-100) for a
  signal to be acted upon. Default is 30. Signals from publishers below this floor are logged but
  carry zero advisory weight.

### 3.4 Kill switch

Any tenant admin may disable all federation participation immediately by setting both
`federation_publish_enabled=false` and `federation_subscribe_enabled=false`. This takes effect on
the next consumer tick (maximum delay: `federation_consumer_block_ms`, default 2000 ms). In-flight
signals already written to the Redis stream by this tenant before the disable are not recalled;
receivers who have already processed them will have their own copies in `federation_signal`.

Platform operators (SENTINEL administrators) may revoke a tenant's participation globally by calling
`POST /internal/admin/federation/revoke/{tenant_id}`, which sets both flags to `false` and records
the revocation in `audit_log_entry`. This is the enforcement action used after a dispute finding of
deliberate false-signalling (see §5).

---

## 4. Reputation System

### 4.1 Score definition

Every publishing tenant has a reputation score in the range [0, 100]. The default score for a newly
admitted publisher is 50. The score is stored in `federation_publisher.reputation` and updated by
the reputation service on every qualifying event.

A score of 100 means the publisher has an unblemished record of confirmed-true signals. A score of
0 means the publisher has been found to consistently produce false or invalid signals and has likely
been revoked.

### 4.2 Score movement

| Event kind | Delta | Condition |
|---|---|---|
| `CONFIRM_TRUE` | +1 | A receiving tenant explicitly confirms a federated signal led to a true positive. |
| `CONFIRM_FALSE` | −5 | A receiving tenant disputes a signal and the investigation finds it was incorrect. |
| `EXPLICIT_COMPLAINT` | −10 | A receiving tenant files a formal complaint about deliberate false-signalling. |
| `SIGNATURE_INVALID` | −2 | A signal's HMAC commit fails verification at the receiver. Indicates key compromise or tampering. |

Score is clamped to [0, 100] after every adjustment. The adjustment function is:

```
new_score = clamp(0, 100, current_score + delta)
```

All reputation events are recorded in `federation_reputation_event` with the event kind, delta,
publisher tenant ID, reporter tenant ID, and timestamp. This table is the authoritative audit trail
for all reputation changes.

### 4.3 Advisory weight reduction

When a publisher's reputation falls below the `federation_low_reputation_threshold` (default 30),
signals from that publisher carry a reduced advisory weight in the detection pipeline. The weight
formula applied by the receiving tenant's scoring service is:

```
effective_delta = federation_advisory_delta      # default 10, if reputation >= threshold
effective_delta = federation_low_reputation_delta  # default 3, if reputation < threshold
```

This means a signal from a trusted publisher raises the receiver's actor score by 10 points; a
signal from a low-reputation publisher raises it by only 3 points. The signal is still logged and
matched — it does not disappear — but its weight is proportionally reduced until the publisher's
reputation recovers or the publisher is revoked.

### 4.4 Publisher onboarding

A new operator joins the federation by:

1. Signing the MOU referencing this document.
2. Submitting a federation application including: platform name, jurisdiction(s), estimated monthly
   active users, contact email for dispute notifications.
3. SENTINEL administrators create a `federation_publisher` record with `reputation=50` and issue
   the tenant's HMAC secret pair.
4. The tenant sets `federation_governance_acknowledged=true` and enables their chosen publish/
   subscribe flags.

### 4.5 Publisher revocation

A publisher is revoked when:

- Their reputation score falls below 10 following confirmed false-signal findings.
- They breach the data minimization commitments in §2.
- They fail to respond to a dispute notification within 14 days.
- A court order or regulatory direction requires their removal.

Revocation sets `federation_publisher.revoked_at` to the current timestamp. All future signals from
the revoked tenant are rejected at the stream consumer level with `signature_invalid` logged to
`audit_log_entry`. Signals already distributed and acted on by receivers are not retracted
automatically; each receiver may purge them manually via the admin API.

---

## 5. Dispute Process

When a receiving tenant believes a federated signal was false or malicious:

**Step 1 — Receiver flags the signal.**
The receiver calls `POST /internal/federation/dispute` with the `federation_signal.id` and a
written description of why the signal is believed to be false. This creates a
`federation_reputation_event` with `reason=dispute_filed` and notifies the publishing tenant via
their registered contact email within 1 hour.

**Step 2 — Publisher notified.**
The publisher receives a notification containing: the signal fields (which they authored), the
reporter's tenant ID (but no information about the specific actor on the receiver's platform), and
the reporter's written description.

**Step 3 — Investigation window.**
The publisher has 7 calendar days to respond with one of:

- **Upheld** — the publisher agrees the signal was erroneous. Score: `CONFIRM_FALSE` (−5) applied
  to publisher.
- **Disputed** — the publisher maintains the signal was correct and provides supporting evidence
  (without disclosing raw actor data). The dispute is escalated to SENTINEL administrators for
  adjudication.
- **No response** — after 7 days without a response, SENTINEL administrators apply `CONFIRM_FALSE`
  automatically and flag the publisher for monitoring.

**Step 4 — Outcome recorded.**
The outcome is appended to `federation_reputation_event` and to the `audit_log_entry` for the
original signal. The receiver is notified of the outcome.

**Step 5 — Escalated adjudication (if applicable).**
When a dispute is escalated, SENTINEL administrators review both sides' submissions within 14 days.
If the signal is found to be deliberately false, `EXPLICIT_COMPLAINT` (−10) is applied and the
publisher is placed on probation. A second upheld complaint within 90 days triggers revocation.

---

## 6. Privacy Impact Summary

### 6.1 Threat model

An attacker who has full access to the federation Redis stream would observe:

- 16-dimensional float vectors (fingerprints).
- HMAC-keyed actor hashes (opaque bytes, 32 bytes each).
- Signal kind labels (strings like `secrecy_request`).
- Timestamps (flagged_at, received_at).
- Publisher tenant IDs (UUIDs).
- HMAC commit bytes.

**What the attacker cannot do with this data:**

- Recover any message content (no raw text is ever placed in the stream).
- Map an actor hash back to a platform identity without both the publishing tenant's HMAC secret
  and actor pepper, which are never transmitted.
- Cross-correlate actor hashes across tenants, because each tenant uses its own HMAC secret and
  pepper — the same real-world actor produces a different hash on every platform.
- Recover the actor's demographic data, platform handle, or device identifiers.

### 6.2 Cryptographic guarantees

**Authenticity.** Every signal carries a `commit` field: an HMAC-SHA256 over the canonical
serialization of the signal fields, computed with the publishing tenant's HMAC secret. Receivers
verify this commit before acting on the signal. A signal that fails verification is rejected and
logged as `signature_invalid`, applying a −2 reputation delta to the publisher.

**Integrity.** The canonical serialization uses deterministic key ordering, ensuring that the same
signal fields always produce the same commit bytes. Any in-transit modification of any field
invalidates the commit.

**Non-repudiation.** The `publisher_tenant_id` is bound into the signed payload. A publisher cannot
later claim they did not originate a signal; the HMAC commit is evidence of origin.

### 6.3 Unavoidable residual risks

**Timing correlation.** An attacker with access to multiple tenants' ingestion streams and the
federation stream can attempt to correlate the timing of a flagging event on one platform with the
appearance of a new federation signal. This correlation attack requires: simultaneous access to
multiple tenants' private ingestion data (a highly privileged position), knowledge of which actors
are being monitored, and the ability to time flagging events. The attack is feasible in theory but
requires capabilities that would constitute a breach of the MOU independent of federation.
Mitigation: future versions may introduce a publish delay jitter.

**Fingerprint inference attack.** A sufficiently sophisticated attacker who (a) controls an actor
on multiple platforms, (b) knows what patterns SENTINEL detects, and (c) can observe which of their
actions trigger a federation signal might, over many iterations, reverse-engineer partial information
about the fingerprint embedding. Feasibility assessment: low. The fingerprint is a 16-dimensional
vector derived from a composite of interaction patterns across time; it is not a simple
transformation of any single message. The signal is published only once per actor crossing a
high-tier threshold (tier 4 minimum by default), limiting iteration opportunities. No mitigation is
planned for v1; Private Set Intersection (§8) would eliminate this residual risk in a future
version.

---

## 7. Governance

### 7.1 Admission of new operators

New operators are admitted to the federation by SENTINEL's federation governance committee, which
must include at least two members: a SENTINEL platform engineer and a legal/compliance
representative. Admission requires:

1. Completed federation application (§4.4).
2. Signed MOU referencing this document by URL and version. The MOU must be countersigned by the
   operator's legal representative.
3. Technical review confirming the operator's SENTINEL deployment meets the minimum version
   requirement for federation protocol support.
4. Governance committee approval.

The signed MOU is stored in SENTINEL's compliance archive. The admission is recorded in
`audit_log_entry` with `event_kind=federation_operator_admitted`.

### 7.2 Removal process

An operator may be removed from the federation by:

- **Voluntary withdrawal.** The operator notifies the governance committee in writing. Their
  publisher record is revoked immediately. They retain their historical signal records in their own
  database but no longer receive or contribute new signals.
- **Involuntary revocation.** Following the revocation criteria in §4.5. The committee votes;
  a majority is sufficient. The operator is notified of the decision and the reasons. An appeal
  may be filed within 14 days, triggering a second vote requiring a supermajority.
- **Regulatory removal.** A court order or regulator instruction requires no committee vote.

Removed operators' historical contributions remain in receivers' `federation_signal` tables.
The governance committee may issue a signal recall notice (advisory, not technically enforced in v1)
recommending receivers purge signals from the removed operator.

### 7.3 Annual audit cadence

The federation network undergoes an annual audit covering:

- **Signal quality audit.** A sample of federated signals (minimum 100 or 10% of annual volume,
  whichever is larger) is reviewed to confirm they meet the data minimization requirements of §2
  and that publisher reputation events accurately reflect signal outcomes.
- **Access control audit.** Verification that `federation_tenant_secret` rows are protected by
  row-level security and that no cross-tenant secret access is possible.
- **Reputation integrity audit.** All reputation events in `federation_reputation_event` for the
  preceding 12 months are reviewed for correctness.
- **Dispute resolution audit.** All disputes filed in the preceding 12 months are reviewed for
  compliance with the 7-day investigation window and correct outcome recording.

The audit findings are recorded in a signed document stored in SENTINEL's compliance archive.
Significant findings must be remediated within 90 days; critical findings (e.g. data minimization
breach) trigger immediate suspension of affected publishers pending remediation.

---

## 8. Open Work and Future Enhancements

The following capabilities are candidates for future versions of the federation protocol. They are
not available in v1 and are not commitments to deliver by any specific date.

**Private Set Intersection (PSI).** In v1, a publisher computes a fingerprint and publishes it.
A receiver stores it and performs local k-NN matching. This means receivers accumulate a growing
set of foreign fingerprint vectors. PSI protocols would allow two tenants to discover which actors
they have in common without either party learning the other's full set. This eliminates the
fingerprint accumulation risk at receivers and removes the fingerprint inference attack surface
described in §6.3.

**Secure aggregation.** For aggregate statistics (e.g. how many federated signals per week match
at a given receiver), secure aggregation protocols allow a coordinator to compute the sum across
all participants without learning any individual participant's contribution. This would enable
federation analytics dashboards without centralizing raw signal counts.

**Homomorphic fingerprint matching.** Fully homomorphic encryption (FHE) schemes can, in principle,
allow a receiver to compute cosine similarity between a query vector and encrypted stored vectors
without decrypting the stored vectors. If feasible at acceptable latency for 16-dimensional
vectors, this would eliminate the need for receivers to hold decrypted fingerprints at all, reducing
data-at-rest exposure and the scope of a breach at the receiver side. Current FHE performance
benchmarks for this vector dimension suggest sub-second matching is achievable; a pilot evaluation
is planned for v2 scoping.

---

*This document is maintained in the SENTINEL repository at `docs/compliance/federation-governance.md`.
It is subject to change; the signed MOU references the version current at signing. Material changes
require re-acknowledgment from all active participants.*
