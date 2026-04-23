// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { BiasAuditTable } from "@/components/bias-audit-table";
import { AuthProvider } from "@/lib/auth-context";
import { writeSession } from "@/lib/storage";

function wrap(node: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  writeSession({
    access_token: "a",
    refresh_token: "r",
    user: { id: "u", tenant_id: "t", email: "m@x.y", role: "admin", display_name: "M" },
  });
  return (
    <QueryClientProvider client={client}>
      <AuthProvider>{node}</AuthProvider>
    </QueryClientProvider>
  );
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("BiasAuditTable", () => {
  it("renders rows and switches group_by", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            group_by: "age_band",
            rows: [{ group: "adult", total_actors: 10, total_flagged: 3, flag_rate: 0.3 }],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            group_by: "jurisdiction",
            rows: [{ group: "US", total_actors: 5, total_flagged: 1, flag_rate: 0.2 }],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );
    vi.stubGlobal("fetch", fetchMock);
    render(wrap(<BiasAuditTable />));
    expect(await screen.findByText(/adult/)).toBeInTheDocument();
    await userEvent.selectOptions(screen.getByLabelText(/group by/i), "jurisdiction");
    await waitFor(() => {
      const lastCall = fetchMock.mock.calls.at(-1);
      expect(String(lastCall?.[0])).toContain("group_by=jurisdiction");
    });
  });
});
