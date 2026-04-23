# Node SDK Quickstart

Target: first event submitted and scored within 30 minutes.

## 1. Install

Build the tarball locally:

```bash
cd sdk/node && npm install && npm run build && npm pack
```

Install it into your project:

```bash
npm install /path/to/sentinel/sdk/node/sentinel-client-0.1.0.tgz
```

Requires Node 20 or newer (uses built-in `fetch` and `node:crypto`).

## 2. Get credentials

You need:

- A tenant API key (`sk_...`) from the SENTINEL dashboard.
- Your tenant UUID.
- The API base URL (for example `https://api.sentinel.example.com`).

Set them in your environment:

```bash
export SENTINEL_API_KEY=sk_live_...
export SENTINEL_BASE_URL=https://api.sentinel.example.com
export SENTINEL_TENANT_ID=00000000-0000-0000-0000-000000000001
```

## 3. Send your first event

Create `send-event.mjs`:

```javascript
import { createHash } from "node:crypto";

import { EventType, SentinelClient } from "@sentinel/client";

function hashUserId(userId) {
  return createHash("sha256").update(userId).digest("hex");
}

const client = new SentinelClient({
  apiKey: process.env.SENTINEL_API_KEY,
  baseUrl: process.env.SENTINEL_BASE_URL
});

const result = await client.events.message({
  tenantId: process.env.SENTINEL_TENANT_ID,
  conversationId: "11111111-1111-1111-1111-111111111111",
  actorExternalIdHash: hashUserId("my-first-user"),
  content: "hello from my first SENTINEL integration",
  timestamp: new Date(),
  eventType: EventType.Message,
  metadata: { platform: "my-app", channel: "dm" }
});

console.log(`tier=${result.tier} score=${result.currentScore} delta=${result.delta}`);
```

Run it:

```bash
node send-event.mjs
```

You should see output like:

```
tier=trusted score=0 delta=0
```

## 4. React to the result

```javascript
import { ResponseTier } from "@sentinel/client";

const order = [
  ResponseTier.Trusted,
  ResponseTier.Watch,
  ResponseTier.ActiveMonitor,
  ResponseTier.Throttle,
  ResponseTier.Restrict,
  ResponseTier.Critical
];

if (order.indexOf(result.tier) >= order.indexOf(ResponseTier.Throttle)) {
  throttleActor(userId);
} else if (order.indexOf(result.tier) >= order.indexOf(ResponseTier.Watch)) {
  flagForReview(userId);
}
```

## 5. Next steps

- Read the [Node API reference](./api-reference-node.md).
- Add [webhook signature verification](./integration-guide.md#webhook-signature-verification).
- Learn about [idempotency and fail-open semantics](./integration-guide.md).
