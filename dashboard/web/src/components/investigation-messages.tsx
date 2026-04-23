// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { formatTimestamp } from "@/lib/format";
import type { InvestigationMessagesResponse } from "@/lib/types";
import { EmptyState } from "./empty-state";
import { InvestigationReasonModal } from "./investigation-reason-modal";

interface Props {
  conversationId: string;
}

export function InvestigationMessages({ conversationId }: Props) {
  const [reason, setReason] = useState<string | null>(null);

  const q = useQuery<InvestigationMessagesResponse>({
    enabled: reason !== null,
    queryKey: ["conv-messages", conversationId, reason],
    queryFn: () =>
      apiFetch<InvestigationMessagesResponse>(
        `/dashboard/api/conversations/${conversationId}/messages?limit=200`,
        { extraHeaders: { "X-Investigation-Reason": reason! } }
      ),
  });

  if (reason === null) {
    return <InvestigationReasonModal onSubmit={(r) => setReason(r)} />;
  }
  if (q.isLoading) return <div className="text-sm text-slate-500">Loading messages…</div>;
  if (q.isError) return <div role="alert" className="text-sm text-red-600">Failed to load messages</div>;
  if (!q.data || q.data.messages.length === 0) return <EmptyState message="No messages in this conversation." />;

  return (
    <div className="flex flex-col gap-2">
      <div className="rounded border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
        Access logged. Reason: <strong>{reason}</strong>
      </div>
      <ul className="flex flex-col gap-2">
        {q.data.messages.map((m) => (
          <li key={m.event_id} className="rounded border border-slate-200 bg-white p-3 text-sm">
            <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
              <span>
                {formatTimestamp(m.timestamp)} · {m.type}
              </span>
              <span>actor {m.actor_id}</span>
            </div>
            <pre className="whitespace-pre-wrap break-words rounded bg-slate-50 p-2 text-xs text-slate-800">
{JSON.stringify(m.content_features, null, 2)}
            </pre>
          </li>
        ))}
      </ul>
    </div>
  );
}
