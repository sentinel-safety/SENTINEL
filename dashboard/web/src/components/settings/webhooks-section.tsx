// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { apiFetch, ApiError } from "@/lib/api-client";
import { formatTimestamp } from "@/lib/format";
import type { WebhookCreateResponse, WebhookListResponse } from "@/lib/types";
import { Button } from "../button";
import { EmptyState } from "../empty-state";
import { ErrorBanner } from "../error-banner";
import { SecretOnceModal } from "../secret-once-modal";
import { TextInput } from "../text-input";

export function WebhooksSection() {
  const qc = useQueryClient();
  const [url, setUrl] = useState("");
  const [eventsText, setEventsText] = useState("");
  const [createError, setCreateError] = useState<string | null>(null);
  const [revealedSecret, setRevealedSecret] = useState<string | null>(null);

  const list = useQuery<WebhookListResponse>({
    queryKey: ["webhooks"],
    queryFn: () => apiFetch<WebhookListResponse>("/dashboard/api/tenant/webhooks"),
  });

  const create = useMutation<WebhookCreateResponse, ApiError, { url: string; events: string[] }>({
    mutationFn: (payload) =>
      apiFetch<WebhookCreateResponse>("/dashboard/api/tenant/webhooks", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: (data) => {
      setRevealedSecret(data.secret);
      setUrl("");
      setEventsText("");
      setCreateError(null);
      qc.invalidateQueries({ queryKey: ["webhooks"] });
    },
    onError: (e) => setCreateError(e.bodyText || `Create failed (${e.status})`),
  });

  const del = useMutation<void, ApiError, string>({
    mutationFn: (id) => apiFetch<void>(`/dashboard/api/tenant/webhooks/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["webhooks"] });
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          const events = eventsText
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean);
          if (events.length === 0) {
            setCreateError("At least one event is required");
            return;
          }
          create.mutate({ url, events });
        }}
        className="flex max-w-xl flex-col gap-3"
      >
        <h3 className="text-sm font-semibold text-slate-800">Register webhook</h3>
        {createError ? <ErrorBanner message={createError} /> : null}
        <TextInput label="URL" type="url" value={url} onChange={(e) => setUrl(e.target.value)} required />
        <TextInput
          label="Event topics (comma-separated, e.g. alert.triggered,actor.tier_change)"
          value={eventsText}
          onChange={(e) => setEventsText(e.target.value)}
          required
        />
        <div>
          <Button type="submit" disabled={create.isPending}>
            {create.isPending ? "Creating…" : "Register"}
          </Button>
        </div>
      </form>

      {list.isLoading ? <div className="text-sm text-slate-500">Loading…</div> : null}
      {list.isError ? <div role="alert" className="text-sm text-red-600">Failed to load webhooks</div> : null}
      {list.data && list.data.webhooks.length === 0 ? <EmptyState message="No webhooks registered." /> : null}
      {list.data && list.data.webhooks.length > 0 ? (
        <div className="overflow-hidden rounded border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-left">
              <tr>
                <th className="px-3 py-2">URL</th>
                <th className="px-3 py-2">Events</th>
                <th className="px-3 py-2">Active</th>
                <th className="px-3 py-2">Created</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {list.data.webhooks.map((w) => (
                <tr key={w.id} className="border-t border-slate-100">
                  <td className="px-3 py-2 break-all">{w.url}</td>
                  <td className="px-3 py-2">{w.events.join(", ")}</td>
                  <td className="px-3 py-2">{w.active ? "yes" : "no"}</td>
                  <td className="px-3 py-2">{formatTimestamp(w.created_at)}</td>
                  <td className="px-3 py-2 text-right">
                    <Button
                      variant="danger"
                      onClick={() => del.mutate(w.id)}
                      disabled={del.isPending}
                    >
                      Delete
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
          title="Webhook"
          secret={revealedSecret}
          onClose={() => setRevealedSecret(null)}
        />
      ) : null}
    </div>
  );
}
