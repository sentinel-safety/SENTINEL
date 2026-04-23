// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ComplianceForm } from "@/components/compliance-form";
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
  (globalThis as unknown as { URL: typeof URL }).URL.createObjectURL = vi.fn(() => "blob:x");
  (globalThis as unknown as { URL: typeof URL }).URL.revokeObjectURL = vi.fn();
});

describe("ComplianceForm", () => {
  it("requires at least one category selected", async () => {
    render(wrap(<ComplianceForm />));
    await userEvent.click(screen.getByRole("button", { name: /export/i }));
    expect(await screen.findByText(/at least one category/i)).toBeInTheDocument();
  });

  it("on success, calls BFF and triggers blob download", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(new Blob(["PK"], { type: "application/zip" }), {
        status: 200,
        headers: { "Content-Type": "application/zip" },
      })
    );
    vi.stubGlobal("fetch", fetchMock);
    render(wrap(<ComplianceForm />));
    await userEvent.type(screen.getByLabelText(/from/i), "2026-04-01T00:00");
    await userEvent.type(screen.getByLabelText(/to/i), "2026-04-30T00:00");
    await userEvent.click(screen.getByLabelText(/audit log/i));
    await userEvent.click(screen.getByRole("button", { name: /export/i }));
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled();
      const call = fetchMock.mock.calls[0];
      expect(String(call[0])).toContain("/dashboard/api/compliance/export");
      expect(call[1].method).toBe("POST");
    });
  });
});
