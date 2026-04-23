// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


import { render } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";
import { describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/",
}));

import { LoginForm } from "@/components/login-form";
import { EmptyState } from "@/components/empty-state";
import { ErrorBanner } from "@/components/error-banner";
import { AuthProvider } from "@/lib/auth-context";

expect.extend(toHaveNoViolations);

function wrap(node: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={client}>
      <AuthProvider>{node}</AuthProvider>
    </QueryClientProvider>
  );
}

describe("dashboard accessibility (axe-core WCAG 2.1 AA baseline)", () => {
  it("login form has no violations", async () => {
    const { container } = render(wrap(<LoginForm />));
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("empty state has no violations", async () => {
    const { container } = render(
      <EmptyState title="No alerts" description="Nothing to review right now." />,
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("error banner has no violations", async () => {
    const { container } = render(<ErrorBanner message="Something failed." />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
