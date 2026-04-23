// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SecretOnceModal } from "@/components/secret-once-modal";

describe("SecretOnceModal", () => {
  it("close button disabled until confirm checkbox", async () => {
    const onClose = vi.fn();
    render(<SecretOnceModal title="API key" secret="sk_abc.xyz" onClose={onClose} />);  // pragma: allowlist secret
    const closeBtn = screen.getByRole("button", { name: /close/i });
    expect(closeBtn).toBeDisabled();
    await userEvent.click(screen.getByLabelText(/saved this secret/i));
    expect(closeBtn).not.toBeDisabled();
    await userEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalled();
  });

  it("displays the secret text", () => {
    render(<SecretOnceModal title="webhook" secret="whsec_xyz" onClose={() => {}} />);  // pragma: allowlist secret
    expect(screen.getByText("whsec_xyz")).toBeInTheDocument();
  });
});
