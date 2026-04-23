// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RoleGate } from "@/components/role-gate";
import { AuthProvider } from "@/lib/auth-context";
import { writeSession } from "@/lib/storage";

function renderWith(role: "admin" | "mod" | "viewer" | "auditor") {
  writeSession({
    access_token: "a",
    refresh_token: "r",
    user: { id: "u", tenant_id: "t", email: "e@x.y", role, display_name: "E" },
  });
  return render(
    <AuthProvider>
      <RoleGate allow={["admin"]}>
        <div data-testid="secret">visible</div>
      </RoleGate>
    </AuthProvider>
  );
}

describe("RoleGate", () => {
  it("renders children when role allowed", () => {
    renderWith("admin");
    expect(screen.getByTestId("secret")).toBeInTheDocument();
  });
  it("hides children when role not allowed", () => {
    renderWith("viewer");
    expect(screen.queryByTestId("secret")).not.toBeInTheDocument();
  });
});
