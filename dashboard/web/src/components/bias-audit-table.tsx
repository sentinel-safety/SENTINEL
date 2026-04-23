// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { formatPercent } from "@/lib/format";
import type { BiasAuditResponse } from "@/lib/types";
import { EmptyState } from "./empty-state";
import { SelectInput } from "./select-input";

export function BiasAuditTable() {
  const [groupBy, setGroupBy] = useState<"age_band" | "jurisdiction">("age_band");

  const q = useQuery<BiasAuditResponse>({
    queryKey: ["bias-audit", groupBy],
    queryFn: () => apiFetch<BiasAuditResponse>(`/dashboard/api/bias-audit?group_by=${groupBy}`),
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-end gap-3">
        <SelectInput
          label="Group by"
          value={groupBy}
          onChange={(e) => setGroupBy(e.target.value as "age_band" | "jurisdiction")}
        >
          <option value="age_band">Age band</option>
          <option value="jurisdiction">Jurisdiction</option>
        </SelectInput>
      </div>

      {q.isLoading ? <div className="text-sm text-slate-500">Loading…</div> : null}
      {q.isError ? <div role="alert" className="text-sm text-red-600">Failed to load bias audit</div> : null}
      {q.data && q.data.rows.length === 0 ? <EmptyState message="No data to display." /> : null}

      {q.data && q.data.rows.length > 0 ? (
        <div className="overflow-hidden rounded border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-left">
              <tr>
                <th className="px-3 py-2">Group</th>
                <th className="px-3 py-2">Total actors</th>
                <th className="px-3 py-2">Flagged (T≥2)</th>
                <th className="px-3 py-2">Flag rate</th>
              </tr>
            </thead>
            <tbody>
              {q.data.rows.map((r) => (
                <tr key={r.group} className="border-t border-slate-100">
                  <td className="px-3 py-2">{r.group}</td>
                  <td className="px-3 py-2">{r.total_actors}</td>
                  <td className="px-3 py-2">{r.total_flagged}</td>
                  <td className="px-3 py-2">{formatPercent(r.flag_rate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
