// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { apiFetch, ApiError } from "@/lib/api-client";
import type { TenantSettings } from "@/lib/types";
import { Button } from "../button";
import { ErrorBanner } from "../error-banner";
import { TextInput } from "../text-input";

export function GeneralSection() {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [tier, setTier] = useState("");
  const [jurisdictions, setJurisdictions] = useState("");
  const [retention, setRetention] = useState<number>(365);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState<boolean>(false);

  const q = useQuery<TenantSettings>({
    queryKey: ["tenant-settings"],
    queryFn: () => apiFetch<TenantSettings>("/dashboard/api/tenant/settings"),
  });

  useEffect(() => {
    if (q.data) {
      setName(q.data.name);
      setTier(q.data.tier);
      setJurisdictions(q.data.compliance_jurisdictions.join(", "));
      setRetention(q.data.data_retention_days);
    }
  }, [q.data]);

  const save = useMutation<TenantSettings, ApiError, TenantSettings>({
    mutationFn: (payload) =>
      apiFetch<TenantSettings>("/dashboard/api/tenant/settings", {
        method: "PUT",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      setSaved(true);
      setError(null);
      qc.invalidateQueries({ queryKey: ["tenant-settings"] });
    },
    onError: (e) => setError(e.bodyText || `Save failed (${e.status})`),
  });

  if (q.isLoading) return <div className="text-sm text-slate-500">Loading…</div>;
  if (q.isError) return <div role="alert" className="text-sm text-red-600">Failed to load tenant settings</div>;

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        setSaved(false);
        save.mutate({
          name,
          tier,
          compliance_jurisdictions: jurisdictions
            .split(",")
            .map((x) => x.trim())
            .filter(Boolean),
          data_retention_days: Number(retention),
        });
      }}
      className="flex max-w-xl flex-col gap-3"
    >
      {error ? <ErrorBanner message={error} /> : null}
      {saved ? (
        <div role="status" className="rounded border border-green-300 bg-green-50 p-2 text-xs text-green-800">
          Saved.
        </div>
      ) : null}
      <TextInput label="Tenant name" value={name} onChange={(e) => setName(e.target.value)} required />
      <TextInput label="Tier" value={tier} onChange={(e) => setTier(e.target.value)} required />
      <TextInput
        label="Compliance jurisdictions (comma-separated)"
        value={jurisdictions}
        onChange={(e) => setJurisdictions(e.target.value)}
      />
      <TextInput
        label="Data retention (days)"
        type="number"
        min={1}
        max={3650}
        value={String(retention)}
        onChange={(e) => setRetention(Number(e.target.value))}
      />
      <div>
        <Button type="submit" disabled={save.isPending}>
          {save.isPending ? "Saving…" : "Save"}
        </Button>
      </div>
    </form>
  );
}
