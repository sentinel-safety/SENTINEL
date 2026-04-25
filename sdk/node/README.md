# @sentinel-safety/client

Official Node.js/TypeScript SDK for the SENTINEL behavioral intelligence API.

## Install

```bash
npm install @sentinel-safety/client
```

## Quickstart

```typescript
import { SentinelClient } from "@sentinel-safety/client";

const client = new SentinelClient({
  apiKey: process.env.SENTINEL_API_KEY!,
  baseUrl: "https://api.sentinel.example.com"
});

const result = await client.events.message({
  tenantId: "00000000-0000-0000-0000-000000000001",
  conversationId: "00000000-0000-0000-0000-000000000002",
  actorExternalIdHash: "a".repeat(64),
  content: "hello",
  timestamp: new Date()
});

console.log(result.tier, result.currentScore);
```

Reference: [`docs/sdk-docs/`](../../docs/sdk-docs/). Platform context: [root README](../../README.md).
