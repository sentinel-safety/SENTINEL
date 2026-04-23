// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-client";
import { formatScore, formatTier, formatTimestamp } from "@/lib/format";
import type { ActorDetail } from "@/lib/types";

export function ActorOverview({ actorId }: { actorId: string }) {
  const q = useQuery<ActorDetail>({
    queryKey: ["actor", actorId],
    queryFn: () => apiFetch<ActorDetail>(`/dashboard/api/actors/${actorId}`),
  });
  if (q.isLoading) return <div className="text-sm text-slate-500">Loading…</div>;
  if (q.isError) return <div role="alert" className="text-sm text-red-600">Failed to load actor</div>;
  const a = q.data!;
  return (
    <dl className="grid grid-cols-2 gap-4 rounded border border-slate-200 bg-white p-4 text-sm">
      <div>
        <dt className="font-medium text-slate-700">Actor ID</dt>
        <dd className="text-slate-900">{a.actor_id}</dd>
      </div>
      <div>
        <dt className="font-medium text-slate-700">Age band</dt>
        <dd className="text-slate-900">{a.claimed_age_band}</dd>
      </div>
      <div>
        <dt className="font-medium text-slate-700">Current tier</dt>
        <dd className="text-slate-900">{formatTier(a.tier)}</dd>
      </div>
      <div>
        <dt className="font-medium text-slate-700">Score</dt>
        <dd className="text-slate-900">{formatScore(a.current_score)}</dd>
      </div>
      <div>
        <dt className="font-medium text-slate-700">Tier entered</dt>
        <dd className="text-slate-900">{formatTimestamp(a.tier_entered_at)}</dd>
      </div>
      <div>
        <dt className="font-medium text-slate-700">Account created</dt>
        <dd className="text-slate-900">{formatTimestamp(a.account_created_at)}</dd>
      </div>
    </dl>
  );
}
