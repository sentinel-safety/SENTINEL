# SENTINEL SDK Documentation

Official SDKs for the SENTINEL behavioral intelligence REST API.

## Packages

| Language | Package | Source |
|---|---|---|
| Python | `sentinel-python` (wheel built locally) | [`sdk/python/`](../../sdk/python/) |
| Node / TypeScript | `@sentinel/client` (tarball built locally) | [`sdk/node/`](../../sdk/node/) |

## Index

- [Python quickstart](./quickstart-python.md)
- [Node quickstart](./quickstart-node.md)
- [Python API reference](./api-reference-python.md)
- [Node API reference](./api-reference-node.md)
- [Integration guide](./integration-guide.md) — platforms, webhooks, idempotency, fail-open

## Scope

Both SDKs wrap `POST /v1/events` (submit events, read back a `ScoreResult`) and provide webhook signature verification. They do **not** hash actor identifiers (caller pre-hashes SHA-256 hex), do **not** manage webhook registration (use the dashboard), and do **not** retry 4xx client errors except 429. On complete API unreachability after retries, both return a `trusted`-tier fallback `ScoreResult` and log a warning so the calling platform keeps serving traffic.

See the [root README](../../README.md) for platform context.
