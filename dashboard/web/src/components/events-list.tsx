// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { formatTimestamp } from "@/lib/format";
import type { EventListResponse } from "@/lib/types";
import { EmptyState } from "./empty-state";

export function EventsList({ actorId }: { actorId: string }) {
  const q = useQuery<EventListResponse>({
    queryKey: ["actor-events", actorId],
    queryFn: () => apiFetch<EventListResponse>(`/dashboard/api/actors/${actorId}/events?limit=100`),
  });
  if (q.isLoading) return <div className="text-sm text-slate-500">Loading…</div>;
  if (q.isError) return <div role="alert" className="text-sm text-red-600">Failed to load events</div>;
  if (!q.data || q.data.events.length === 0) return <EmptyState message="No events yet." />;

  return (
    <div className="overflow-hidden rounded border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="bg-slate-100 text-left">
          <tr>
            <th className="px-3 py-2">Timestamp</th>
            <th className="px-3 py-2">Type</th>
            <th className="px-3 py-2">Score Δ</th>
            <th className="px-3 py-2">Conversation</th>
          </tr>
        </thead>
        <tbody>
          {q.data.events.map((e) => (
            <tr key={e.id} className="border-t border-slate-100 hover:bg-slate-50">
              <td className="px-3 py-2">{formatTimestamp(e.timestamp)}</td>
              <td className="px-3 py-2">{e.type}</td>
              <td className="px-3 py-2">{e.score_delta >= 0 ? `+${e.score_delta}` : e.score_delta}</td>
              <td className="px-3 py-2">
                <Link
                  href={`/actors/${actorId}/investigation/${e.conversation_id}`}
                  className="text-blue-700 underline"
                >
                  {e.conversation_id}
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
