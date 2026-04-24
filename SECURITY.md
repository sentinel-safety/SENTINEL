✅——————# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅ Yes    |

Security fixes are applied to the latest release on `main`.

---

## Reporting a Vulnerability

**Do not report security vulnerabilities through public GitHub issues.**

Report privately to: **sentinel.childsafety@gmail.com**  
Subject line: `[SECURITY] Brief description`

### What to include

- Description of the vulnerability and its potential impact
- Steps to reproduce or proof-of-concept
- Which component is affected (API, scoring engine, audit log, federation layer, SDK, etc.)
- Suggested severity: critical / high / medium / low

### Response timeline

- **Acknowledgement:** within 48 hours
- **Initial assessment:** within 5 business days
- **Fix timeline:** severity-dependent; critical issues are prioritised immediately
- **Disclosure:** coordinated with the reporter

Security researchers are credited in release notes unless anonymity is preferred.

---

## High-Priority Areas

Given SENTINEL's purpose, these components are especially critical:

**Audit log integrity** — Vulnerabilities enabling undetected modification or deletion of tamper-evident audit logs undermine legal defensibility. Treat as critical.

**Federation privacy** — Vulnerabilities causing the federation layer to transmit raw message content or user identities (rather than encrypted behavioral signatures only) are a serious privacy breach. Treat as critical.

**Fairness gate bypass** — Vulnerabilities allowing a model that failed demographic parity checks to deploy are high severity.

**API authentication** — Unauthorized event ingestion or risk score retrieval affects safety decisions made by platforms relying on SENTINEL.

---

## Out of Scope

- Vulnerabilities in third-party dependencies (report upstream)
- Theoretical attacks without a practical exploit path
- Social engineering
- Issues requiring physical server access

---

## Security Architecture Notes

- Audit logs use cryptographic chaining — tampering with historical entries is detectable
- The federation layer operates on encrypted behavioral signatures; raw message content never leaves the originating platform
- All API endpoints require authentication; see `docs/api/authentication.md`
- The fairness gate runs as a pre-deployment check; models failing parity tests are rejected before serving predictions

---

*SENTINEL is not a substitute for professional security review of your platform. Platforms remain responsible for their own security posture.*
