import { beforeEach, describe, expect, it, jest } from "@jest/globals";

import { SentinelClient } from "../src/client.js";
import { EventType, ResponseTier } from "../src/types.js";

type FetchMock = jest.Mock<typeof fetch>;

function mockOkOnce(fetchMock: FetchMock, body: unknown): void {
  fetchMock.mockImplementationOnce(async () =>
    new Response(JSON.stringify(body), {
      status: 200,
      headers: { "content-type": "application/json" }
    })
  );
}

describe("SentinelClient.events.message", () => {
  let fetchMock: FetchMock;

  beforeEach(() => {
    fetchMock = jest.fn();
  });

  it("posts to /v1/events and parses ScoreResult", async () => {
    mockOkOnce(fetchMock, {
      event_id: "11111111-1111-1111-1111-111111111111",
      current_score: 24,
      previous_score: 12,
      delta: 12,
      tier: "watch",
      signals: []
    });
    const client = new SentinelClient({
      apiKey: "sk_test", // pragma: allowlist secret
      baseUrl: "https://api.sentinel.test",
      fetchImpl: fetchMock as unknown as typeof fetch
    });
    const result = await client.events.message({
      tenantId: "00000000-0000-0000-0000-000000000001",
      conversationId: "00000000-0000-0000-0000-000000000002",
      actorExternalIdHash: "a".repeat(64),
      content: "hi",
      timestamp: new Date("2026-04-20T12:00:00Z")
    });
    expect(result.tier).toBe(ResponseTier.Watch);
    expect(result.currentScore).toBe(24);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("https://api.sentinel.test/v1/events");
    const headers = new Headers(init.headers);
    expect(headers.get("authorization")).toBe("Bearer sk_test");
    const body = JSON.parse(init.body as string) as Record<string, unknown>;
    expect(body.event_type).toBe("message");
    expect(body.actor_external_id_hash).toBe("a".repeat(64));
    expect(typeof body.idempotency_key).toBe("string");
  });

  it("rejects malformed hash before fetching", async () => {
    const client = new SentinelClient({
      apiKey: "sk", // pragma: allowlist secret
      baseUrl: "https://api.sentinel.test",
      fetchImpl: fetchMock as unknown as typeof fetch
    });
    await expect(
      client.events.message({
        tenantId: "00000000-0000-0000-0000-000000000001",
        conversationId: "00000000-0000-0000-0000-000000000002",
        actorExternalIdHash: "not-hex",
        content: "x",
        timestamp: new Date("2026-04-20T12:00:00Z")
      })
    ).rejects.toThrow(/actor_external_id_hash/);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("uses caller-provided idempotency key", async () => {
    mockOkOnce(fetchMock, {
      event_id: "11111111-1111-1111-1111-111111111111",
      current_score: 0,
      previous_score: 0,
      delta: 0,
      tier: "trusted",
      signals: []
    });
    const client = new SentinelClient({
      apiKey: "sk", // pragma: allowlist secret
      baseUrl: "https://api.sentinel.test",
      fetchImpl: fetchMock as unknown as typeof fetch
    });
    await client.events.message({
      tenantId: "00000000-0000-0000-0000-000000000001",
      conversationId: "00000000-0000-0000-0000-000000000002",
      actorExternalIdHash: "a".repeat(64),
      content: "hi",
      timestamp: new Date("2026-04-20T12:00:00Z"),
      idempotencyKey: "client-provided"
    });
    const body = JSON.parse(
      (fetchMock.mock.calls[0]?.[1] as RequestInit).body as string
    ) as Record<string, unknown>;
    expect(body.idempotency_key).toBe("client-provided");
  });

  it("serializes event type image", async () => {
    mockOkOnce(fetchMock, {
      event_id: "11111111-1111-1111-1111-111111111111",
      current_score: 0,
      previous_score: 0,
      delta: 0,
      tier: "trusted",
      signals: []
    });
    const client = new SentinelClient({
      apiKey: "sk", // pragma: allowlist secret
      baseUrl: "https://api.sentinel.test",
      fetchImpl: fetchMock as unknown as typeof fetch
    });
    await client.events.message({
      tenantId: "00000000-0000-0000-0000-000000000001",
      conversationId: "00000000-0000-0000-0000-000000000002",
      actorExternalIdHash: "a".repeat(64),
      content: "[image]",
      timestamp: new Date("2026-04-20T12:00:00Z"),
      eventType: EventType.Image
    });
    const body = JSON.parse(
      (fetchMock.mock.calls[0]?.[1] as RequestInit).body as string
    ) as Record<string, unknown>;
    expect(body.event_type).toBe("image");
  });
});
