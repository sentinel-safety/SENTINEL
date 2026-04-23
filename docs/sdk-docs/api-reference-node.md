# Node SDK API Reference

Module: `@sentinel/client`, version 0.1.0. Requires Node 20+.

## `SentinelClient`

```typescript
new SentinelClient({
  apiKey: string;
  baseUrl: string;
  timeoutMs?: number;              // default 10000
  retryAttempts?: number;          // default 3
  retryBaseSeconds?: number;       // default 0.5
  retryCapSeconds?: number;        // default 30
  fetchImpl?: typeof fetch;        // inject your own fetch
  logger?: { warn: (msg: string) => void };
});
```

### Properties

- `events: EventsAPI` — see below.

## `client.events.message(...)`

```typescript
client.events.message({
  tenantId: string;                              // UUID
  conversationId: string;                        // UUID
  actorExternalIdHash: string;                   // lowercase hex SHA-256, 64 chars
  content: string;                               // up to 20000 chars
  timestamp: Date;                               // any JS Date
  eventType?: EventType;                         // defaults to EventType.Message
  targetActorExternalIdHashes?: readonly string[];
  metadata?: Record<string, unknown>;
  idempotencyKey?: string;                       // if omitted, SDK generates uuid4
}): Promise<ScoreResult>;
```

### Thrown errors

| Error | When |
|---|---|
| `Error` | Malformed hash regex, empty `apiKey` / `baseUrl`. |
| `AuthError` | HTTP 401 / 403. **Not retried.** |
| All other 5xx / transport / timeout errors | Fail-open: resolves with a trusted fallback `ScoreResult` after `retryAttempts`. |

## Types

### `ScoreResult`

```typescript
interface ScoreResult {
  currentScore: number;         // 0-100
  previousScore: number;
  delta: number;
  tier: ResponseTier;
  reasoning: Reasoning | null;
}
```

### `ResponseTier`

String-valued `enum`:

```typescript
enum ResponseTier {
  Trusted = "trusted",
  Watch = "watch",
  ActiveMonitor = "active_monitor",
  Throttle = "throttle",
  Restrict = "restrict",
  Critical = "critical"
}
```

### `EventType`

```typescript
enum EventType {
  Message = "message",
  Image = "image",
  FriendRequest = "friend_request",
  Gift = "gift",
  ProfileChange = "profile_change",
  VoiceClip = "voice_clip"
}
```

### `ActionKind`

`enum` with values `none`, `silent_log`, `review_queue`, `throttle_dm_to_minors`, `disable_media_to_minors`, `require_approval_to_friend_minor`, `restrict_to_public_posts`, `block_dm_to_minors`, `account_warning`, `suspend`, `mandatory_report`.

### `Reasoning`

```typescript
interface Reasoning {
  actorId: string;
  tenantId: string;
  scoreChange: number;
  newScore: number;
  newTier: ResponseTier;
  primaryDrivers: readonly PrimaryDriver[];
  context: string;
  recommendedActionSummary: string;
  generatedAt: string;            // ISO 8601
  nextReviewAt: string | null;
}
```

### `PrimaryDriver`

```typescript
interface PrimaryDriver {
  pattern: string;
  patternId: string;
  confidence: number;             // 0.0 - 1.0
  evidence: string;
}
```

### `RecommendedAction`

```typescript
interface RecommendedAction {
  kind: ActionKind;
  description: string;
  parameters: Record<string, unknown>;
}
```

## Errors

```
SentinelError
├── AuthError
├── RateLimitError { retryAfterSeconds: number | null }
├── TimeoutError
└── ServerError { statusCode: number }
```

## Webhook verification

```typescript
verifyWebhookSignature({
  header: string;                             // raw X-Sentinel-Signature
  secret: string;                             // tenant webhook secret
  body: Buffer | Uint8Array | string;         // raw request body
  now: Date;
  skewSeconds?: number;                       // default 300
}): void;
```

Throws `WebhookSignatureError` on any mismatch. Returns `void` on success.

**Pass the raw body.** Re-serializing JSON WILL break the signature because the server signs exact bytes (`orjson` with sorted keys).
