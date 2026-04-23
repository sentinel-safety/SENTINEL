import { beforeEach, describe, expect, it, jest } from "@jest/globals";

import { SentinelClient } from "../src/client.js";
import { AuthError } from "../src/errors.js";
import { ResponseTier } from "../src/types.js";

type FetchMock = jest.Mock<typeof fetch>;

function makeClient(fetchMock: FetchMock): SentinelClient {
  return new SentinelClient({
    apiKey: "sk", // pragma: allowlist secret
    baseUrl: "https://api.sentinel.test",
    retryAttempts: 3,
    retryBaseSeconds: 0,
    retryCapSeconds: 0,
    fetchImpl: fetchMock as unknown as typeof fetch,
    logger: { warn: () => undefined }
  });
}

describe("fail-open + retry", () => {
  let fetchMock: FetchMock;

  beforeEach(() => {
    fetchMock = jest.fn();
  });

  it("returns fallback on repeated 500s", async () => {
    fetchMock.mockImplementation(async () => new Response("boom", { status: 503 }));
    const result = await makeClient(fetchMock).events.message({
      tenantId: "00000000-0000-0000-0000-000000000001",
      conversationId: "00000000-0000-0000-0000-000000000002",
      actorExternalIdHash: "a".repeat(64),
      content: "x",
      timestamp: new Date("2026-04-20T12:00:00Z")
    });
    expect(result.tier).toBe(ResponseTier.Trusted);
    expect(result.currentScore).toBe(0);
    expect(result.reasoning).toBeNull();
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("returns fallback on transport error", async () => {
    fetchMock.mockImplementation(async () => {
      throw new TypeError("fetch failed");
    });
    const result = await makeClient(fetchMock).events.message({
      tenantId: "00000000-0000-0000-0000-000000000001",
      conversationId: "00000000-0000-0000-0000-000000000002",
      actorExternalIdHash: "a".repeat(64),
      content: "x",
      timestamp: new Date("2026-04-20T12:00:00Z")
    });
    expect(result.tier).toBe(ResponseTier.Trusted);
  });

  it("retries on 500 then succeeds", async () => {
    fetchMock
      .mockImplementationOnce(async () => new Response("boom", { status: 500 }))
      .mockImplementationOnce(async () => new Response("boom", { status: 500 }))
      .mockImplementationOnce(
        async () =>
          new Response(
            JSON.stringify({
              event_id: "11111111-1111-1111-1111-111111111111",
              current_score: 14,
              previous_score: 10,
              delta: 4,
              tier: "watch",
              signals: []
            }),
            { status: 200, headers: { "content-type": "application/json" } }
          )
      );
    const result = await makeClient(fetchMock).events.message({
      tenantId: "00000000-0000-0000-0000-000000000001",
      conversationId: "00000000-0000-0000-0000-000000000002",
      actorExternalIdHash: "a".repeat(64),
      content: "x",
      timestamp: new Date("2026-04-20T12:00:00Z")
    });
    expect(result.tier).toBe(ResponseTier.Watch);
    expect(result.currentScore).toBe(14);
  });

  it("auth error does not retry", async () => {
    fetchMock.mockImplementation(async () => new Response("nope", { status: 401 }));
    await expect(
      makeClient(fetchMock).events.message({
        tenantId: "00000000-0000-0000-0000-000000000001",
        conversationId: "00000000-0000-0000-0000-000000000002",
        actorExternalIdHash: "a".repeat(64),
        content: "x",
        timestamp: new Date("2026-04-20T12:00:00Z")
      })
    ).rejects.toThrow(AuthError);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
