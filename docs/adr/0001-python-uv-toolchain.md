# ADR-0001: Python 3.12 + uv as the project toolchain

- Status: Accepted
- Date: 2026-04-01
- Deciders: Platform team

## Context

SENTINEL is a behavioral intelligence platform composed of many Python services sharing common domain models. We need a language runtime and a dependency manager that:

- Support modern typing features (`StrEnum`, `typing.Self`, `TypeAliasType`) used throughout the codebase.
- Install reproducibly on CI and in Docker images.
- Resolve the complex dependency graph (SQLAlchemy 2.x, Pydantic 2.x, OpenTelemetry SDK, FastAPI, orjson) in seconds, not minutes.
- Keep development overhead close to zero for contributors.

## Decision

- **Runtime:** Python 3.12.
- **Dependency manager:** [`uv`](https://docs.astral.sh/uv/) (Astral) with `uv.lock` committed.

All services, shared libraries, and test harnesses share a single `pyproject.toml` / `uv.lock` pair at the repository root.

## Alternatives considered

- **Poetry** — slower resolution, weaker lockfile semantics for mixed-version deps, separate CLI from ruff/mypy pipelines.
- **pip + pip-tools** — workable but manual; resolution is not incremental, and lockfiles are per-extra rather than unified.
- **Python 3.11** — lacks per-interpreter improvements (f-string parsing, error traces) and misses 3.12-only typing features we use today.

## Consequences

### Positive

- Single, very fast dependency resolver shared across local dev, CI, and Docker builds.
- Modern typing lets us ship `FrozenModel`, `StrEnum`, and PEP 695 type aliases without workarounds.
- `uv sync --frozen --no-dev --no-install-project` keeps service images small and deterministic.

### Negative / Trade-offs

- `uv` is new; edge-case bugs or breaking releases could disrupt CI. Mitigated by pinning the uv binary version in CI and Docker images.
- Contributors unfamiliar with uv need a short onboarding note (see `docs/getting-started.md`).

### Neutral

- Single workspace means any dep change requires cross-service validation; offset by CI running the entire test suite per commit.
