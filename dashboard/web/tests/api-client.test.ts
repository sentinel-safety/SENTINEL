// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch, ApiError } from "@/lib/api-client";
import { writeSession, readSession, clearSession } from "@/lib/storage";

const baseSession = {
  access_token: "access-1",
  refresh_token: "refresh-1",
  user: {
    id: "u1",
    tenant_id: "t1",
    email: "a@b.c",
    role: "admin" as const,
    display_name: "A",
  },
};

beforeEach(() => {
  clearSession();
  vi.restoreAllMocks();
});

describe("apiFetch", () => {
  it("attaches bearer token", async () => {
    writeSession(baseSession);
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "Content-Type": "application/json" } })
    );
    vi.stubGlobal("fetch", fetchMock);
    await apiFetch("/dashboard/api/ping");
    const call = fetchMock.mock.calls[0];
    const headers = call[1].headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer access-1");
  });

  it("throws ApiError on non-2xx without retry when not 401", async () => {
    writeSession(baseSession);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("bad", { status: 500 }))
    );
    await expect(apiFetch("/dashboard/api/x")).rejects.toBeInstanceOf(ApiError);
  });

  it("on 401 calls refresh then retries with new access token", async () => {
    writeSession(baseSession);
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response("unauth", { status: 401 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ access_token: "access-2" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      );
    vi.stubGlobal("fetch", fetchMock);
    const result = await apiFetch<{ ok: boolean }>("/dashboard/api/x");
    expect(result).toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(readSession()?.access_token).toBe("access-2");
  });

  it("on 401 + refresh 401 clears session and throws", async () => {
    writeSession(baseSession);
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response("unauth", { status: 401 }))
      .mockResolvedValueOnce(new Response("unauth", { status: 401 }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(apiFetch("/dashboard/api/x")).rejects.toBeInstanceOf(ApiError);
    expect(readSession()).toBeNull();
  });

  it("supports asBlob for binary responses", async () => {
    writeSession(baseSession);
    const blob = new Blob(["PK\u0003\u0004"], { type: "application/zip" });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(blob, { status: 200, headers: { "Content-Type": "application/zip" } }))
    );
    const out = await apiFetch<Blob>("/dashboard/api/x", { asBlob: true });
    expect(out).toBeInstanceOf(Blob);
  });
});
