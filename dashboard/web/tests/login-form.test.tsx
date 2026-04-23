// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginForm } from "@/components/login-form";
import { AuthProvider } from "@/lib/auth-context";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

function wrap(node: React.ReactNode) {
  return <AuthProvider>{node}</AuthProvider>;
}

describe("LoginForm", () => {
  it("shows validation when submitting empty", async () => {
    render(wrap(<LoginForm />));
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
  });

  it("submits and stores session on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            access_token: "a",
            refresh_token: "r",
            user: { id: "u", tenant_id: "t", email: "m@x.y", role: "admin", display_name: "M" },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      )
    );
    render(wrap(<LoginForm />));
    await userEvent.type(screen.getByLabelText(/email/i), "m@x.y");
    await userEvent.type(screen.getByLabelText(/password/i), "secret123");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    await waitFor(() => {
      expect(localStorage.getItem("sentinel_session")).toContain("m@x.y");
    });
  });

  it("shows error on 401", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("unauth", { status: 401 }))
    );
    render(wrap(<LoginForm />));
    await userEvent.type(screen.getByLabelText(/email/i), "a@b.c");
    await userEvent.type(screen.getByLabelText(/password/i), "wrong");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/invalid/i);
  });
});
