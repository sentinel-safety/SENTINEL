// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-client";
import { formatTimestamp } from "@/lib/format";
import type { ReasoningListResponse } from "@/lib/types";
import { EmptyState } from "./empty-state";

export function ReasoningList({ actorId }: { actorId: string }) {
  const q = useQuery<ReasoningListResponse>({
    queryKey: ["actor-reasoning", actorId],
    queryFn: () => apiFetch<ReasoningListResponse>(`/dashboard/api/actors/${actorId}/reasoning?limit=50`),
  });
  if (q.isLoading) return <div className="text-sm text-slate-500">Loading…</div>;
  if (q.isError) return <div role="alert" className="text-sm text-red-600">Failed to load reasoning</div>;
  if (!q.data || q.data.reasoning.length === 0) return <EmptyState message="No reasoning captured." />;
  return (
    <ul className="flex flex-col gap-3">
      {q.data.reasoning.map((r) => (
        <li key={r.id} className="rounded border border-slate-200 bg-white p-3">
          <div className="mb-1 text-xs text-slate-500">{formatTimestamp(r.created_at)}</div>
          <pre className="whitespace-pre-wrap break-words rounded bg-slate-50 p-2 text-xs text-slate-800">
{JSON.stringify(r.reasoning_json, null, 2)}
          </pre>
        </li>
      ))}
    </ul>
  );
}
