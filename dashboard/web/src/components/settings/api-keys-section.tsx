// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { apiFetch, ApiError } from "@/lib/api-client";
import { formatTimestamp } from "@/lib/format";
import type {
  ApiKeyCreateRequest,
  ApiKeyCreateResponse,
  ApiKeyListResponse,
} from "@/lib/types";
import { Button } from "../button";
import { EmptyState } from "../empty-state";
import { ErrorBanner } from "../error-banner";
import { SecretOnceModal } from "../secret-once-modal";
import { SelectInput } from "../select-input";
import { TextInput } from "../text-input";

export function ApiKeysSection() {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [scope, setScope] = useState<"read" | "write" | "admin">("read");
  const [createError, setCreateError] = useState<string | null>(null);
  const [revealedSecret, setRevealedSecret] = useState<string | null>(null);

  const list = useQuery<ApiKeyListResponse>({
    queryKey: ["api-keys"],
    queryFn: () => apiFetch<ApiKeyListResponse>("/dashboard/api/tenant/api-keys"),
  });

  const create = useMutation<ApiKeyCreateResponse, ApiError, ApiKeyCreateRequest>({
    mutationFn: (payload) =>
      apiFetch<ApiKeyCreateResponse>("/dashboard/api/tenant/api-keys", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: (data) => {
      setRevealedSecret(data.secret);
      setName("");
      setCreateError(null);
      qc.invalidateQueries({ queryKey: ["api-keys"] });
    },
    onError: (e) => setCreateError(e.bodyText || `Create failed (${e.status})`),
  });

  const revoke = useMutation<void, ApiError, string>({
    mutationFn: (id) => apiFetch<void>(`/dashboard/api/tenant/api-keys/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["api-keys"] }),
  });

  return (
    <div className="flex flex-col gap-6">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (!name.trim()) {
            setCreateError("Name is required");
            return;
          }
          create.mutate({ name: name.trim(), scope });
        }}
        className="flex max-w-xl flex-col gap-3"
      >
        <h3 className="text-sm font-semibold text-slate-800">Create API key</h3>
        {createError ? <ErrorBanner message={createError} /> : null}
        <TextInput label="Name" value={name} onChange={(e) => setName(e.target.value)} required />
        <SelectInput
          label="Scope"
          value={scope}
          onChange={(e) => setScope(e.target.value as "read" | "write" | "admin")}
        >
          <option value="read">read</option>
          <option value="write">write</option>
          <option value="admin">admin</option>
        </SelectInput>
        <div>
          <Button type="submit" disabled={create.isPending}>
            {create.isPending ? "Creating…" : "Create"}
          </Button>
        </div>
      </form>

      {list.isLoading ? <div className="text-sm text-slate-500">Loading…</div> : null}
      {list.isError ? <div role="alert" className="text-sm text-red-600">Failed to load API keys</div> : null}
      {list.data && list.data.api_keys.length === 0 ? <EmptyState message="No API keys." /> : null}

      {list.data && list.data.api_keys.length > 0 ? (
        <div className="overflow-hidden rounded border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-left">
              <tr>
                <th className="px-3 py-2">Name</th>
                <th className="px-3 py-2">Prefix</th>
                <th className="px-3 py-2">Scope</th>
                <th className="px-3 py-2">Created</th>
                <th className="px-3 py-2">Last used</th>
                <th className="px-3 py-2">Revoked</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {list.data.api_keys.map((k) => (
                <tr key={k.id} className="border-t border-slate-100">
                  <td className="px-3 py-2">{k.name}</td>
                  <td className="px-3 py-2 font-mono text-xs">{k.prefix}</td>
                  <td className="px-3 py-2">{k.scope}</td>
                  <td className="px-3 py-2">{formatTimestamp(k.created_at)}</td>
                  <td className="px-3 py-2">{formatTimestamp(k.last_used_at)}</td>
                  <td className="px-3 py-2">{formatTimestamp(k.revoked_at)}</td>
                  <td className="px-3 py-2 text-right">
                    <Button
                      variant="danger"
                      onClick={() => revoke.mutate(k.id)}
                      disabled={revoke.isPending || k.revoked_at !== null}
                    >
                      {k.revoked_at ? "Revoked" : "Revoke"}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {revealedSecret ? (
        <SecretOnceModal
          title="API key"
          secret={revealedSecret}
          onClose={() => setRevealedSecret(null)}
        />
      ) : null}
    </div>
  );
}
