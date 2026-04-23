import { createHash } from "node:crypto";

import { EventType, SentinelClient } from "../src/index.js";

function hashUserId(userId: string): string {
  return createHash("sha256").update(userId).digest("hex");
}

async function main(): Promise<void> {
  const apiKey = process.env.SENTINEL_API_KEY;
  if (!apiKey) {
    throw new Error("SENTINEL_API_KEY is not set");
  }
  const baseUrl = process.env.SENTINEL_BASE_URL ?? "https://api.sentinel.example.com";
  const client = new SentinelClient({ apiKey, baseUrl });
  const result = await client.events.message({
    tenantId: process.env.SENTINEL_TENANT_ID ?? "00000000-0000-0000-0000-000000000001",
    conversationId: "11111111-1111-1111-1111-111111111111",
    actorExternalIdHash: hashUserId("platform-user-42"),
    content: "Hello from the SENTINEL Node SDK!",
    timestamp: new Date(),
    eventType: EventType.Message,
    metadata: { platform: "example-app", channel: "dm" }
  });
  console.log(`tier=${result.tier} score=${result.currentScore} delta=${result.delta}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
