// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


import { render, screen, act } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AuthProvider, useAuth } from "@/lib/auth-context";
import type { StoredSession } from "@/lib/storage";

const session: StoredSession = {
  access_token: "a",
  refresh_token: "r",
  user: { id: "u", tenant_id: "t", email: "e@x.y", role: "admin", display_name: "E" },
};

function Probe() {
  const auth = useAuth();
  return (
    <div>
      <span data-testid="email">{auth.user?.email ?? "none"}</span>
      <button onClick={() => auth.setSession(session)}>login</button>
      <button onClick={() => auth.logout()}>logout</button>
    </div>
  );
}

describe("AuthProvider", () => {
  it("starts logged out", () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );
    expect(screen.getByTestId("email")).toHaveTextContent("none");
  });

  it("setSession persists and exposes user", async () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );
    await act(async () => {
      screen.getByText("login").click();
    });
    expect(screen.getByTestId("email")).toHaveTextContent("e@x.y");
    expect(localStorage.getItem("sentinel_session")).toContain("e@x.y");
  });

  it("logout clears user and storage", async () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );
    await act(async () => {
      screen.getByText("login").click();
    });
    await act(async () => {
      screen.getByText("logout").click();
    });
    expect(screen.getByTestId("email")).toHaveTextContent("none");
    expect(localStorage.getItem("sentinel_session")).toBeNull();
  });
});
