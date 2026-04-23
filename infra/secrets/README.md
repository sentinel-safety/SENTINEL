# Secrets Management

Invariant: **no plaintext secret lives in the repository, the container image, or a long-lived environment file.**

## Development

Copy `.env.example` to `.env` (gitignored) and fill in local throwaway credentials for docker-compose Postgres / Redis / Qdrant. Use the `fake` LLM provider locally; real Anthropic/OpenAI/NCMEC keys must never land in a developer `.env`.

## Production runtime

Envelope encryption: each secret is AES-256-GCM encrypted with a data-encryption key (DEK); every DEK is wrapped by a key-encryption key (KEK) held in a managed KMS (AWS KMS, GCP KMS, or Vault Transit). Storage is one secret per `(tenant, service, purpose)` in AWS Secrets Manager / GCP Secret Manager / Vault KV v2. Services read secrets into process environment at start, never to disk, never logged (structlog has an allowlist-based redaction formatter).

## Rotation (minimum cadence)

| Secret | Cadence |
|---|---|
| Database passwords | 90 days |
| LLM API keys | 30 days, or immediately on suspected leak |
| Webhook signing secrets | 180 days, on-demand per tenant |
| KEKs | KMS-managed, 365 days |

Rotation is atomic with a 10-minute dual-accept overlap; rotation events land in the audit log.

## Pre-commit

`detect-secrets` runs on every commit against `.secrets.baseline`. Never use `# pragma: allowlist secret` to mask a real production value.

See the [root README](../../README.md) for platform context.
