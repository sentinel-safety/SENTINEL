# SENTINEL

**Behavioral child safety intelligence for any platform.**

[![CI](https://github.com/sentinel-safety/SENTINEL/actions/workflows/ci.yml/badge.svg)](https://github.com/sentinel-safety/SENTINEL/actions)
[![License](https://img.shields.io/badge/license-Custom%20%E2%86%92%20Apache%202.0%20in%202046-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://python.org)

SENTINEL detects child grooming on digital platforms by watching **how behavior evolves over time** — not what words appear in individual messages. Keyword filters are evaded daily. Behavioral patterns are not.

> **v1.0 released April 23, 2026.** Free for platforms under $100k revenue and all non-commercial/research use.

---

## The Problem

Most platforms protecting children today are using a word list.

Grooming is a process, not a moment. It takes weeks of trust-building, relationship manipulation, and behavioral escalation — none of which triggers a keyword filter. Predators have adapted: they avoid flagged words, use coded language, and keep every individual message below detection thresholds. By the time a filter fires, harm has usually already begun.

SENTINEL watches the trajectory, not the moment.

---

## Quick Start

**Docker Compose (recommended):**

```bash
git clone https://github.com/sentinel-safety/SENTINEL
cd SENTINEL
cp .env.example .env
docker compose up -d
```

SENTINEL is running. Send your first event:

```python
from sentinel import SentinelClient

client = SentinelClient(api_key="your_key", base_url="http://localhost:8080")

result = client.events.ingest({
    "platform_user_id": "user_84721",
    "recipient_id":     "user_10392",
    "channel_type":     "direct_message",
    "timestamp":        "2026-04-24T09:41:00Z",
    "message_length":   142
})

print(result.risk_score)    # → 87
print(result.tier)          # → "critical"
print(result.explanation)   # → plain-language behavioral signals
```

**Node.js:**

```js
import { SentinelClient } from '@sentinel-safety/sdk'

const sentinel = new SentinelClient({ apiKey: 'your_key' })

const result = await sentinel.events.ingest({
  platformUserId: 'user_84721',
  recipientId:    'user_10392',
  channelType:    'direct_message',
  timestamp:      new Date().toISOString()
})
```

**Under an hour to first integration.** Full documentation in [`/docs`](docs/).

---

## How It Works

SENTINEL builds a behavioral profile for every user across four signal layers:

| Layer | What It Watches |
|-------|----------------|
| **Linguistic** | How conversation register, vocabulary, and topic focus shift *across sessions* |
| **Graph** | Who communicates with whom, escalation from group→private, multi-account coordination |
| **Temporal** | Contact frequency acceleration, unusual-hours patterns, cross-session dynamics |
| **Fairness** | Demographic parity enforced architecturally — models cannot deploy if they fail |

Each user receives a **risk score (0–100)** with a tier label (`trusted` / `watch` / `restrict` / `critical`) and a **structured plain-language explanation** of every signal that contributed. Moderators see *why*, not just a number.

---

## Key Features

- **Explainable outputs** — every score includes the specific behavioral signals that drove it. Legal defensibility built in.
- **Tamper-evident audit logs** — cryptographically chained, 7-year retention. Usable in legal proceedings. Satisfies regulatory audit requirements.
- **Privacy-preserving federation** — platforms share threat signatures without sharing raw messages or user identities. A predator banned on one federated platform is flagged on others within minutes.
- **Fairness gates** — demographic parity audits run before any model deploys. Deployment is blocked if the model disproportionately flags any group.
- **NCMEC CyberTipline packages** — automatically generated when behavioral indicators meet mandatory reporting thresholds. You file; SENTINEL prepares the structured documentation.
- **13 independent microservices** — deploy incrementally, start with wha you need.
- **Honeypot module** (opt-in) — deploy decoy personas to actively surface and document predatory behavior for legal handoff.

---

## Compliance Coverage

SENTINEL provides compliance infrastructure as **architecture-level features**, not bolt-ons:

| Framework | Deadline | What SENTINEL Provides |
|-----------|----------|------------------------|
| **EU Digital Services Act** | In force | Audit log export, risk assessment docs, proactive harm mitigation, transparency reporting hooks |
| **UK Online Safety Act** | Ofcom register: July 2026 | Ofcom-compatible audit trails, harm mitigation evidence, platform-level risk assessment |
| **US COPPA (amended 2026)** | April 2026 | Age-gating hooks, parental consent workflow, under-13 data restrictions, NCMEC report generation |
| **GDPR** | In force | Article 17 erasure handling, data minimization, jurisdiction-aware retention |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  INGESTION          ANALYSIS              SCORING    PERSISTENCE  │
│                                                                   │
│  Event API  ──►  Linguistic Engine ──►                           │
│  Python SDK ──►  Graph Analyzer    ──►  Risk Score  ──► Audit Log│
│  Node SDK   ──►  Temporal Analyzer ──►  Explanation ──► Federation│
│             ──►  Fairness Gate     ──►              ──► Compliance│
└─────────────────────────────────────────────────────────────────┘

13 microservices  ·  Python 3.12  ·  Node.js  ·  Docker Compose
PostgreSQL  ·  Redis  ·  Vector DB
```

Each service is independently deployable. Start with event ingestion + risk scoring; add federation and compliance layers when ready.

---

## Who It's For

**Indie game studios and gaming platforms** — COPPA and UKOSA apply if you have minor users. SENTINEL is free under $100k revenue.

**EdTech platforms** — language learning apps, tutoring platforms, school tools. One integration covers the full compliance surface.

**Social platforms and community forums** — EU DSA is in force. UK Online Safety Act duties arrive mid-2026. SENTINEL provides the proactive detection Ofcom requires.

**Academic researchers** — open research dataset (v1, 50 synthetic conversations) available for extension. Modular architecture designed for researchers to swap in alternative models. Free for all academic use.

---

## Research & Dataset

SENTINEL ships with an open research dataset of 50 synthetic grooming conversations (v1). Dataset contributions, methodology critiques, and extensions are welcomed.

The behavioral detection approach builds on the academic literature — particularly work on context determination ([Street et al., 2025](https://arxiv.org/abs/2409.07958)), interdisciplinary cybergrooming reviews ([An et al., 2025](https://arxiv.org/abs/2503.05727)), and meta-analyses of ML detection methods ([Leiva-Bianchi et al., 2025](https://www.nature.com/articles/s41598-024-83003-4)).

A system paper describing SENTINEL's architecture, four-signal behavioral model, fairness enforcement mechanism, and federation protocol is in preparation for arXiv.

Collaboration inquiries: [sentinel.childsafety@gmail.com](mailto:sentinel.childsafety@gmail.com)

---

## Licensing

| Use case | License |
|----------|---------|
| Non-commercial / research / academic | Free |
| Platform with < $100k annual revenue | Free |
| Platform with ≥ $100k annual revenue | Commercial license required |
| SaaS / hosting SENTINEL for others | Commercial license required |

**In 2046, the license automatically converts to Apache 2.0.** This is a long-term commitment to the open-source ecosystem written into the license itself.

Attribution required in production deployments: display "SENTINEL by Sentinel Foundation" in your dashboard and documentation.

Commercial licensing: [sentinel.childsafety@gmail.com](mailto:sentinel.childsafety@gmail.com)

---

## Relationship to Roblox/Sentinel

[Roblox's Sentinel](https://github.com/Roblox/Sentinel) is a Python detection *library* for contrastive learning-based rare text detection, running on Roblox's own platform. It is excellent at what it does. This project is different: SENTINEL is a compliance *platform* for other platforms to deploy — providing the audit infrastructure, regulatory compliance, federation, and moderator tooling that production deployments require. The two are complementary: Roblox's detection approach could be integrated as a component of SENTINEL's linguistic signal layer.

---

## Read More

In-depth technical articles on DEV Community:

- [Why Keyword Filters Fail for Child Safety — and What Behavioral Detection Actually Looks Like](https://dev.to/sentinelsafety/why-keyword-filters-fail-for-child-safety-and-what-behavioral-detection-actually-looks-like-3phi)
- [Building Compliance-Native Child Safety: What DSA and UKOSA Actually Require](https://dev.to/sentinelsafety/building-compliance-native-child-safety-what-dsa-and-ukosa-actually-require-11ac)
- [Privacy-Preserving Threat Federation: How Platforms Can Share Intelligence Without Sharing Data](https://dev.to/sentinelsafety/privacy-preserving-threat-federation-how-platforms-can-share-intelligence-without-sharing-data-37g4)
- [Fairness in Child Safety AI: Why Demographic Parity Audits Are Not Optional](https://dev.to/sentinelsafety/fairness-in-child-safety-ai-why-demographic-parity-audits-are-not-optional-3iem)
- [Inside SENTINEL: How 13 Microservices Detect Child Grooming by Behavior, Not Keywords](https://dev.to/sentinelsafety/inside-sentinel-how-13-microservices-detect-child-grooming-by-behavior-not-keywords-42p5)
- [Grooming Operates Over Time: How Behavioral Detection Tracks It](https://dev.to/sentinelsafety/grooming-operates-over-time-heres-how-behavioral-detection-tracks-it-fb1)
- [What EU DSA and UK Online Safety Act Require from Your Platform's Child Safety Infrastructure](https://dev.to/sentinelsafety/what-eu-dsa-and-uk-online-safety-act-require-from-your-platforms-child-safety-infrastructure-3ih6)
- [NCMEC Mandatory Reporting for Online Platforms: What Developers Need to Know](https://dev.to/sentinelsafety/ncmec-mandatory-reporting-for-online-platforms-what-developers-need-to-know-4k74)
- [Add Child Safety to Your Platform in 30 Minutes: A SENTINEL Integration Guide](https://dev.to/sentinelsafety/add-child-safety-to-your-platform-in-30-minutes-a-sentinel-integration-guide-14po)
- [COPPA Compliance for Platform Developers: What the Law Actually Requires and How to Build It](https://dev.to/sentinelsafety/coppa-compliance-for-platform-developers-what-the-law-actually-requires-and-how-to-build-it-391k)
- [False Positives in Child Safety AI: Architecture Tradeoffs and Why They Matter](https://dev.to/sentinelsafety/false-positives-in-child-safety-ai-architecture-tradeoffs-and-why-they-matter-3jln)

---

## Contributing

SENTINEL welcomes contributions across all signal layers, compliance modules, and SDK clients. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines.

Particularly welcome:
- Extensions to individual signal layers (swap in your detection model)
- Additional compliance framework coverage
- Research dataset contributions (documented methodology required)
- SDK clients in additional languages

---

## Contact

- **General / partnerships:** [sentinel.childsafety@gmail.com](mailto:sentinel.childsafety@gmail.com)
- **Security vulnerabilities:** See [`SECURITY.md`](SECURITY.md)
- **Research collaboration:** [sentinel.childsafety@gmail.com](mailto:sentinel.childsafety@gmail.com)

---

*SENTINEL is not a substitute for human moderators, legal counsel, or mandatory reporting obligations. Platforms remain legally responsible for their own compliance.*
