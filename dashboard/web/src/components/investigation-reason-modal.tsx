// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { useState } from "react";
import { Button } from "./button";

interface Props {
  onSubmit: (reason: string) => void;
}

export function InvestigationReasonModal({ onSubmit }: Props) {
  const [reason, setReason] = useState("");
  const trimmed = reason.trim();
  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-slate-900/40 p-4">
      <div role="dialog" aria-modal="true" className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
        <h2 className="mb-2 text-lg font-semibold">Investigation access</h2>
        <p className="mb-4 text-sm text-slate-600">
          Viewing conversation content is logged to the audit trail. Please state the reason for access.
        </p>
        <label htmlFor="investigation-reason" className="text-sm font-medium text-slate-700">
          Reason
        </label>
        <textarea
          id="investigation-reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          rows={3}
          className="mt-1 w-full rounded border border-slate-300 p-2 text-sm focus:border-slate-500 focus:outline-none"
          placeholder="e.g. Fraud investigation FI-2026-123"
        />
        <div className="mt-4 flex justify-end gap-2">
          <Button disabled={trimmed.length === 0} onClick={() => onSubmit(trimmed)}>
            View messages
          </Button>
        </div>
      </div>
    </div>
  );
}
