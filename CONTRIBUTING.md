# Contributing to SENTINEL

Thank you for your interest in contributing to SENTINEL. This project exists to make child safety technology accessible to every platform that needs it. Contributions that extend that mission are welcome.

## Ways to Contribute

### Signal layer extensions
SENTINEL's architecture is designed to be modular. Each signal layer (linguistic, graph, temporal, fairness) can be extended or replaced with alternative detection approaches. If you have a better model for any signal layer, we want to know about it.

### SDK clients
Official SDKs exist for Python and Node.js. Community-maintained SDKs for other languages are encouraged:
- Ruby (Rails/Sinatra platforms) — see issue #9
- Go (microservices/cloud-native) — see issue #13
- PHP, Java, Rust, etc.

See the existing SDKs in `sdk/` for the interface contract to implement.

### Compliance framework coverage
SENTINEL currently covers EU DSA, UK Online Safety Act, COPPA, and GDPR. Coverage for additional jurisdictions (Australia eSafety, Canadian PIPEDA, etc.) is in scope.

### Observability and tooling
Grafana/Kibana dashboards, Prometheus metrics, alerting integrations — see issue #11.

### Research dataset contributions
The v1 dataset contains 50 synthetic annotated grooming conversations. Expanding and validating this dataset is one of the highest-leverage contributions possible. See issue #12 for contribution guidelines and methodology requirements.

### Bug reports and feature requests
Use the issue templates. Be specific. Include logs where relevant (redact any PII or conversation content).

---

## Development Setup

```bash
git clone https://github.com/sentinel-safety/SENTINEL
cd SENTINEL
cp .env.example .env
docker compose up -d
```

Run the test suite:
```bash
make test
```

Run linting:
```bash
make lint
```

See the `Makefile` for all available targets.

---

## Contribution Standards

### Code quality
- All PRs must pass CI (linting + tests) before review
- New detection logic should include unit tests
- Behavioral signal changes should include a rationale explaining the research basis

### Fairness requirement
Any PR that modifies detection logic must include a demographic parity analysis showing the change does not introduce or worsen disparate impact. This is not optional. The fairness gate exists for a reason.

### Privacy
- No real conversation content in test fixtures — use synthetic data only
- No PII in logs, error messages, or commit history
- The federation layer must never transmit raw message content

### Documentation
- Public API changes require documentation updates
- New signal layers require a `METHODOLOGY.md` entry explaining the behavioral research basis

---

## Pull Request Process

1. Open an issue first for significant changes — alignment before implementation saves everyone time
2. Fork the repo and create a branch from `main`
3. Make your changes with tests
4. Ensure `make test` and `make lint` pass
5. Open a PR with a clear description of what changed and why
6. A maintainer will review within 7 days

For questions before opening a PR, use [GitHub Discussions](https://github.com/sentinel-safety/SENTINEL/discussions).

---

## Code of Conduct

This project is focused on protecting children. We hold contributors to a high standard of professional conduct. Disrespectful, discriminatory, or bad-faith behavior will result in removal from the project.

---

## Contact

Research collaboration or significant contribution proposals: sentinel.childsafety@gmail.com
