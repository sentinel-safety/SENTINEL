// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { formatScore, formatTier, formatTimestamp } from "@/lib/format";
import type { AlertListResponse } from "@/lib/types";
import { Button } from "./button";
import { EmptyState } from "./empty-state";
import { SelectInput } from "./select-input";

export function AlertsTable() {
  const [minTier, setMinTier] = useState<number>(1);
  const [offset, setOffset] = useState<number>(0);
  const limit = 50;

  const query = useQuery<AlertListResponse>({
    queryKey: ["alerts", minTier, offset],
    queryFn: () =>
      apiFetch<AlertListResponse>(
        `/dashboard/api/alerts?min_tier=${minTier}&limit=${limit}&offset=${offset}`
      ),
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-end gap-3">
        <SelectInput
          label="Minimum tier"
          value={String(minTier)}
          onChange={(e) => {
            setOffset(0);
            setMinTier(Number(e.target.value));
          }}
        >
          <option value="0">T0+</option>
          <option value="1">T1+</option>
          <option value="2">T2+</option>
          <option value="3">T3+</option>
          <option value="4">T4+</option>
          <option value="5">T5</option>
        </SelectInput>
      </div>

      {query.isLoading ? <div className="text-sm text-slate-500">Loading…</div> : null}
      {query.isError ? <div role="alert" className="text-sm text-red-600">Failed to load alerts</div> : null}

      {query.data && query.data.alerts.length === 0 ? (
        <EmptyState message="No alerts match the filter." />
      ) : null}

      {query.data && query.data.alerts.length > 0 ? (
        <div className="overflow-hidden rounded border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-left">
              <tr>
                <th className="px-3 py-2">Actor</th>
                <th className="px-3 py-2">Tier</th>
                <th className="px-3 py-2">Score</th>
                <th className="px-3 py-2">Age band</th>
                <th className="px-3 py-2">Entered tier</th>
                <th className="px-3 py-2">Updated</th>
              </tr>
            </thead>
            <tbody>
              {query.data.alerts.map((a) => (
                <tr key={a.actor_id} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-3 py-2">
                    <Link href={`/actors/${a.actor_id}`} className="text-blue-700 underline">
                      {a.actor_id}
                    </Link>
                  </td>
                  <td className="px-3 py-2">{formatTier(a.tier)}</td>
                  <td className="px-3 py-2">{formatScore(a.current_score)}</td>
                  <td className="px-3 py-2">{a.claimed_age_band}</td>
                  <td className="px-3 py-2">{formatTimestamp(a.tier_entered_at)}</td>
                  <td className="px-3 py-2">{formatTimestamp(a.last_updated)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <div className="flex items-center gap-2">
        <Button variant="secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - limit))}>
          Previous
        </Button>
        <span className="text-sm text-slate-600">Offset {offset}</span>
        <Button
          variant="secondary"
          disabled={(query.data?.alerts.length ?? 0) < limit}
          onClick={() => setOffset(offset + limit)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
