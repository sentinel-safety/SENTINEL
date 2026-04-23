// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { InvestigationReasonModal } from "@/components/investigation-reason-modal";

describe("InvestigationReasonModal", () => {
  it("disables submit until reason is non-empty", async () => {
    const onSubmit = vi.fn();
    render(<InvestigationReasonModal onSubmit={onSubmit} />);
    const btn = screen.getByRole("button", { name: /view messages/i });
    expect(btn).toBeDisabled();
    await userEvent.type(screen.getByLabelText(/reason/i), "fraud check");
    expect(btn).not.toBeDisabled();
    await userEvent.click(btn);
    expect(onSubmit).toHaveBeenCalledWith("fraud check");
  });

  it("rejects whitespace-only reason", async () => {
    const onSubmit = vi.fn();
    render(<InvestigationReasonModal onSubmit={onSubmit} />);
    await userEvent.type(screen.getByLabelText(/reason/i), "   ");
    expect(screen.getByRole("button", { name: /view messages/i })).toBeDisabled();
  });
});
