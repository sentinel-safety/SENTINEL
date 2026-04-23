// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { apiFetch, ApiError } from "@/lib/api-client";
import type { TenantActionConfigResponse } from "@/lib/types";
import { Button } from "../button";
import { ErrorBanner } from "../error-banner";
import { SelectInput } from "../select-input";

export function ActionConfigSection() {
  const qc = useQueryClient();
  const [mode, setMode] = useState<"advisory" | "auto_enforce">("advisory");
  const [overridesText, setOverridesText] = useState<string>("{}");
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);

  const q = useQuery<TenantActionConfigResponse>({
    queryKey: ["tenant-action-config"],
    queryFn: () => apiFetch<TenantActionConfigResponse>("/dashboard/api/tenant/action-config"),
  });

  useEffect(() => {
    if (q.data) {
      setMode(q.data.mode);
      setOverridesText(JSON.stringify(q.data.action_overrides, null, 2));
    }
  }, [q.data]);

  const save = useMutation<TenantActionConfigResponse, ApiError, TenantActionConfigResponse>({
    mutationFn: (payload) =>
      apiFetch<TenantActionConfigResponse>("/dashboard/api/tenant/action-config", {
        method: "PUT",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      setSaved(true);
      setError(null);
      qc.invalidateQueries({ queryKey: ["tenant-action-config"] });
    },
    onError: (e) => setError(e.bodyText || `Save failed (${e.status})`),
  });

  if (q.isLoading) return <div className="text-sm text-slate-500">Loading…</div>;
  if (q.isError) return <div role="alert" className="text-sm text-red-600">Failed to load action config</div>;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaved(false);
    setParseError(null);
    let parsed: Record<string, string[]>;
    try {
      parsed = JSON.parse(overridesText) as Record<string, string[]>;
      if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
        throw new Error("must be an object");
      }
    } catch (err) {
      setParseError(`Invalid JSON: ${(err as Error).message}`);
      return;
    }
    save.mutate({ mode, action_overrides: parsed });
  }

  return (
    <form onSubmit={handleSubmit} className="flex max-w-xl flex-col gap-3">
      {error ? <ErrorBanner message={error} /> : null}
      {saved ? (
        <div role="status" className="rounded border border-green-300 bg-green-50 p-2 text-xs text-green-800">
          Saved.
        </div>
      ) : null}
      <SelectInput
        label="Mode"
        value={mode}
        onChange={(e) => setMode(e.target.value as "advisory" | "auto_enforce")}
      >
        <option value="advisory">advisory</option>
        <option value="auto_enforce">auto_enforce</option>
      </SelectInput>
      <div className="flex flex-col gap-1">
        <label htmlFor="action-overrides" className="text-sm font-medium text-slate-700">
          Action overrides (JSON object: tier → actions[])
        </label>
        <textarea
          id="action-overrides"
          value={overridesText}
          onChange={(e) => setOverridesText(e.target.value)}
          rows={8}
          className="rounded border border-slate-300 bg-white p-2 font-mono text-xs focus:border-slate-500 focus:outline-none"
        />
        {parseError ? <span className="text-xs text-red-600">{parseError}</span> : null}
      </div>
      <div>
        <Button type="submit" disabled={save.isPending}>
          {save.isPending ? "Saving…" : "Save"}
        </Button>
      </div>
    </form>
  );
}
