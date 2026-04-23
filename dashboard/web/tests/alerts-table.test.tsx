// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { AlertsTable } from "@/components/alerts-table";
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

describe("AlertsTable", () => {
  it("renders alert rows", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            alerts: [
              {
                actor_id: "a-1",
                current_score: 72,
                tier: 3,
                tier_entered_at: "2026-04-10T00:00:00Z",
                last_updated: "2026-04-20T00:00:00Z",
                claimed_age_band: "adult",
              },
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      )
    );
    render(wrap(<AlertsTable />));
    expect(await screen.findByText(/a-1/i)).toBeInTheDocument();
    expect(screen.getAllByText(/T3/).length).toBeGreaterThan(0);
  });

  it("changing min_tier refetches", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ alerts: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );
    vi.stubGlobal("fetch", fetchMock);
    render(wrap(<AlertsTable />));
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const select = screen.getByLabelText(/minimum tier/i);
    await userEvent.selectOptions(select, "3");
    await waitFor(() => {
      const lastCall = fetchMock.mock.calls.at(-1);
      expect(String(lastCall?.[0])).toContain("min_tier=3");
    });
  });

  it("shows empty state when no rows", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ alerts: [] }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
    );
    render(wrap(<AlertsTable />));
    expect(await screen.findByText(/no alerts/i)).toBeInTheDocument();
  });
});
