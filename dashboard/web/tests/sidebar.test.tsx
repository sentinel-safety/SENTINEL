// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Sidebar } from "@/components/sidebar";
import { AuthProvider } from "@/lib/auth-context";
import { writeSession } from "@/lib/storage";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/alerts",
  useSearchParams: () => new URLSearchParams(),
}));

function renderAs(role: "admin" | "mod" | "viewer" | "auditor") {
  writeSession({
    access_token: "a",
    refresh_token: "r",
    user: { id: "u", tenant_id: "t", email: "e@x.y", role, display_name: "E" },
  });
  return render(
    <AuthProvider>
      <Sidebar />
    </AuthProvider>
  );
}

describe("Sidebar", () => {
  it("admin sees Settings", () => {
    renderAs("admin");
    expect(screen.getByRole("link", { name: /settings/i })).toBeInTheDocument();
  });

  it("mod does not see Settings", () => {
    renderAs("mod");
    expect(screen.queryByRole("link", { name: /settings/i })).not.toBeInTheDocument();
  });

  it("viewer sees no links", () => {
    renderAs("viewer");
    expect(screen.queryAllByRole("link")).toHaveLength(0);
  });

  it("auditor sees audit log", () => {
    renderAs("auditor");
    expect(screen.getByRole("link", { name: /audit log/i })).toBeInTheDocument();
  });
});
