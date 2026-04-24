# Press & Media — SENTINEL

## One-sentence description

SENTINEL is an open-source behavioral intelligence platform that detects child grooming on digital platforms by watching how relationships form and escalate over time, rather than scanning messages for flagged words.

---

## Key facts

- **Released:** April 2026 — v1.0 initial public release
- **License:** Free for platforms under $100k annual revenue and all non-commercial/research use. Commercial license for larger platforms. License converts to Apache 2.0 in 2046.
- **Language:** Python 3.12 with Node.js SDK
- **Architecture:** 13 microservices, Docker Compose, REST API
- **Time to first integration:** Under one hour
- **Compliance:** EU Digital Services Act, UK Online Safety Act, COPPA
- **Regulatory milestone:** Ofcom's July 2026 categorisation register will bring mid-tier platforms into scope for proactive child safety requirements SENTINEL is designed to address
- **Dataset:** v1 ships with 50 synthetic annotated grooming conversation examples; designed for academic contribution
- **GitHub:** https://github.com/sentinel-safety/SENTINEL

---

## The problem SENTINEL solves

Platform trust and safety teams have relied on keyword filters since the early days of social media. Predators adapted years ago: they use coded language, avoid flagged terms, and take weeks or months to build trust before harmful interactions escalate. By the time a keyword filter triggers, harm is often already in progress.

Behavioral detection — watching how relationships form over time rather than scanning individual messages — is the approach the academic literature has supported for years. The problem has been infrastructure: no open, deployable, compliance-ready platform existed for platforms that aren't Facebook-scale.

SENTINEL is that platform.

---

## How it works

SENTINEL tracks four behavioral signal types across sessions:

**Linguistic signals:** How conversation style and vocabulary shift over multiple interactions. Grooming language evolves — SENTINEL watches for those shifts across the full arc of a relationship, not just individual messages.

**Graph signals:** Who is communicating with whom, at what frequency, and whether patterns suggest coordinated targeting (multiple accounts approaching one minor-identified account).

**Temporal signals:** Escalation velocity, contact frequency changes, cross-session relationship development. Grooming follows predictable temporal escalation patterns that are detectable before overt harm occurs.

**Fairness signals:** Before any detection model can deploy, it must pass a demographic parity audit. Models that flag one demographic group disproportionately cannot ship. This is enforced at the architecture level, not applied post-hoc.

Every risk score (0-100) includes a plain-language explanation of which specific behavioral signals triggered it. Moderators see why a user was flagged, not a number. This matters for moderator judgment, for reducing burnout from opaque systems, and for legal defensibility.

---

## Key features for compliance teams

- Tamper-evident, cryptographically chained audit logs with 7-year retention
- GDPR erasure handling built in
- COPPA data retention compliance
- NCMEC CyberTipline evidence package generation (for mandatory reporting to the National Center for Missing and Exploited Children)
- Privacy-preserving cross-platform federation: platforms share threat signatures without sharing raw messages or user identities

---

## On the naming

Roblox independently released a library also called "Sentinel" (github.com/Roblox/Sentinel) in August 2025. It is a Python contrastive learning library for detection on Roblox's own platform, not a deployable compliance platform for third parties. Roblox's Sentinel and SENTINEL address different layers of the same problem and are potentially complementary.

---

## Quotes for attribution

"Every platform deserves world-class child safety. SENTINEL is the open-source standard — the infrastructure that only FAANG could previously afford to build, available for any platform building communities where children are present."
— Sentinel Foundation

"Grooming is a behavioral process, not a vocabulary problem. Keyword filters catch the symptom. Behavioral detection addresses the cause."
— Sentinel Foundation

---

## Press contact

**Email:** sentinel.childsafety@gmail.com
**GitHub:** https://github.com/sentinel-safety/SENTINEL
**GitHub Discussions (FAQ):** https://github.com/sentinel-safety/SENTINEL/discussions/15

We respond to media inquiries within 24 hours.

---

## Background reading

- Published dev.to article: [Why Keyword Filters Fail for Child Safety](https://dev.to/sentinelsafety/why-keyword-filters-fail-for-child-safety-and-what-behavioral-detection-actually-looks-like-3phi)
- GitHub Discussions FAQ: https://github.com/sentinel-safety/SENTINEL/discussions/15
- Key academic reference: An, Wisniewski, Cho, Huang et al. — "Cybergrooming Unveiled: A Systematic Review and Meta-Analysis" (arXiv:2503.05727, March 2026)

---

*SENTINEL is a project of the Sentinel Foundation. This is v1 — the first public release. We are honest that no large community of production deployments exists yet. The technology is real; the community is at the beginning.*
