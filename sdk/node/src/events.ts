import { webcrypto } from "node:crypto";

import {
  AuthError,
  RateLimitError,
  SentinelError,
  ServerError,
  TimeoutError
} from "./errors.js";
import { computeBackoff, parseRetryAfter } from "./retry.js";
import {
  EventType,
  MessageEventInput,
  ResponseTier,
  ScoreResult
} from "./types.js";

const HASH_PATTERN = /^[a-f0-9]{64}$/;

function requireHash(label: string, value: string): void {
  if (!HASH_PATTERN.test(value)) {
    throw new Error(`${label} must be a lowercase hex SHA256 string (64 chars, [a-f0-9])`);
  }
}

function randomUuid(): string {
  const bytes = new Uint8Array(16);
  const source = (globalThis.crypto ?? webcrypto) as Crypto;
  source.getRandomValues(bytes);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

function fallbackResult(): ScoreResult {
  return {
    currentScore: 0,
    previousScore: 0,
    delta: 0,
    tier: ResponseTier.Trusted,
    reasoning: null
  };
}

function parseScoreResult(payload: Record<string, unknown>): ScoreResult {
  const current = Number(payload.current_score ?? 0);
  const delta = Number(payload.delta ?? 0);
  const previous = Number(payload.previous_score ?? Math.max(0, current - delta));
  const tier = String(payload.tier ?? "trusted") as ResponseTier;
  const reasoning = (payload.reasoning ?? null) as ScoreResult["reasoning"];
  return { currentScore: current, previousScore: previous, delta, tier, reasoning };
}

async function sleep(seconds: number): Promise<void> {
  if (seconds <= 0) return;
  await new Promise((resolve) => setTimeout(resolve, seconds * 1000));
}

export interface EventsAPIDeps {
  baseUrl: string;
  apiKey: string;
  userAgent: string;
  timeoutMs: number;
  retryAttempts: number;
  retryBaseSeconds: number;
  retryCapSeconds: number;
  fetchImpl: typeof fetch;
  logger: { warn: (msg: string) => void };
}

export class EventsAPI {
  private readonly deps: EventsAPIDeps;

  constructor(deps: EventsAPIDeps) {
    this.deps = deps;
  }

  async message(input: MessageEventInput): Promise<ScoreResult> {
    requireHash("actor_external_id_hash", input.actorExternalIdHash);
    for (const target of input.targetActorExternalIdHashes ?? []) {
      requireHash("target_actor_external_id_hashes[*]", target);
    }
    const body = {
      idempotency_key: input.idempotencyKey ?? randomUuid(),
      tenant_id: input.tenantId,
      conversation_id: input.conversationId,
      actor_external_id_hash: input.actorExternalIdHash,
      target_actor_external_id_hashes: Array.from(input.targetActorExternalIdHashes ?? []),
      event_type: (input.eventType ?? EventType.Message).toString(),
      timestamp: input.timestamp.toISOString(),
      content: input.content,
      metadata: input.metadata ?? {}
    };
    return this.sendWithRetries(body);
  }

  private async sendWithRetries(body: Record<string, unknown>): Promise<ScoreResult> {
    let lastError: Error | null = null;
    for (let attempt = 1; attempt <= this.deps.retryAttempts; attempt++) {
      try {
        const response = await this.doFetch(body);
        if (response.status >= 200 && response.status < 300) {
          const json = (await response.json()) as Record<string, unknown>;
          return parseScoreResult(json);
        }
        if (response.status === 401 || response.status === 403) {
          throw new AuthError(`${response.status} authentication failure`);
        }
        if (response.status === 429) {
          const retryAfter = parseRetryAfter(response.headers.get("retry-after"), new Date());
          lastError = new RateLimitError("429 rate limited", retryAfter);
          if (attempt < this.deps.retryAttempts) {
            const backoff = computeBackoff(attempt, this.deps.retryBaseSeconds, this.deps.retryCapSeconds);
            const wait = retryAfter !== null ? Math.min(this.deps.retryCapSeconds, retryAfter) : backoff;
            await sleep(wait);
            continue;
          }
          break;
        }
        if (response.status >= 500) {
          lastError = new ServerError(`${response.status} server error`, response.status);
          if (attempt < this.deps.retryAttempts) {
            await sleep(computeBackoff(attempt, this.deps.retryBaseSeconds, this.deps.retryCapSeconds));
            continue;
          }
          break;
        }
        throw new SentinelError(`unexpected status ${response.status}`);
      } catch (err) {
        if (err instanceof AuthError) {
          throw err;
        }
        lastError = err instanceof Error ? err : new SentinelError(String(err));
        if (attempt >= this.deps.retryAttempts) break;
        await sleep(computeBackoff(attempt, this.deps.retryBaseSeconds, this.deps.retryCapSeconds));
      }
    }
    this.deps.logger.warn(
      `sentinel fail-open: returning trusted fallback after ${this.deps.retryAttempts} attempts (${lastError?.message ?? "unknown"})`
    );
    return fallbackResult();
  }

  private async doFetch(body: Record<string, unknown>): Promise<Response> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.deps.timeoutMs);
    try {
      return await this.deps.fetchImpl(`${this.deps.baseUrl}/v1/events`, {
        method: "POST",
        headers: {
          authorization: `Bearer ${this.deps.apiKey}`,
          "user-agent": this.deps.userAgent,
          "content-type": "application/json"
        },
        body: JSON.stringify(body),
        signal: controller.signal
      });
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        throw new TimeoutError("request timed out");
      }
      throw err;
    } finally {
      clearTimeout(timer);
    }
  }
}
