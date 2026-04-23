// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { formatTimestamp } from "@/lib/format";
import type { AuditEntryListResponse } from "@/lib/types";
import { Button } from "./button";
import { EmptyState } from "./empty-state";
import { TextInput } from "./text-input";

interface Filters {
  actor_id: string;
  event_type: string;
  from: string;
  to: string;
}

const EMPTY: Filters = { actor_id: "", event_type: "", from: "", to: "" };

function toQuery(f: Filters, offset: number, limit: number): string {
  const p = new URLSearchParams();
  if (f.actor_id.trim()) p.set("actor_id", f.actor_id.trim());
  if (f.event_type.trim()) p.set("event_type", f.event_type.trim());
  if (f.from.trim()) p.set("from", new Date(f.from).toISOString());
  if (f.to.trim()) p.set("to", new Date(f.to).toISOString());
  p.set("limit", String(limit));
  p.set("offset", String(offset));
  return p.toString();
}

export function AuditLogTable() {
  const [filters, setFilters] = useState<Filters>(EMPTY);
  const [applied, setApplied] = useState<Filters>(EMPTY);
  const [offset, setOffset] = useState(0);
  const limit = 100;

  const q = useQuery<AuditEntryListResponse>({
    queryKey: ["audit-log", applied, offset],
    queryFn: () => apiFetch<AuditEntryListResponse>(`/dashboard/api/audit-log?${toQuery(applied, offset, limit)}`),
  });

  return (
    <div className="flex flex-col gap-4">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setOffset(0);
          setApplied(filters);
        }}
        className="grid grid-cols-4 gap-3"
      >
        <TextInput
          label="Actor ID"
          value={filters.actor_id}
          onChange={(e) => setFilters({ ...filters, actor_id: e.target.value })}
        />
        <TextInput
          label="Event type"
          value={filters.event_type}
          onChange={(e) => setFilters({ ...filters, event_type: e.target.value })}
        />
        <TextInput
          label="From"
          type="datetime-local"
          value={filters.from}
          onChange={(e) => setFilters({ ...filters, from: e.target.value })}
        />
        <TextInput
          label="To"
          type="datetime-local"
          value={filters.to}
          onChange={(e) => setFilters({ ...filters, to: e.target.value })}
        />
        <div className="col-span-4 flex gap-2">
          <Button type="submit">Apply</Button>
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              setFilters(EMPTY);
              setApplied(EMPTY);
              setOffset(0);
            }}
          >
            Reset
          </Button>
        </div>
      </form>

      {q.isLoading ? <div className="text-sm text-slate-500">Loading…</div> : null}
      {q.isError ? <div role="alert" className="text-sm text-red-600">Failed to load audit log</div> : null}

      {q.data && q.data.entries.length === 0 ? <EmptyState message="No audit entries match the filters." /> : null}

      {q.data && q.data.entries.length > 0 ? (
        <div className="overflow-hidden rounded border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-left">
              <tr>
                <th className="px-3 py-2">Seq</th>
                <th className="px-3 py-2">Timestamp</th>
                <th className="px-3 py-2">Type</th>
                <th className="px-3 py-2">Actor</th>
                <th className="px-3 py-2">Details</th>
                <th className="px-3 py-2">Hash</th>
              </tr>
            </thead>
            <tbody>
              {q.data.entries.map((e) => (
                <tr key={e.id} className="border-t border-slate-100 align-top">
                  <td className="px-3 py-2 font-mono text-xs">{e.sequence}</td>
                  <td className="px-3 py-2">{formatTimestamp(e.timestamp)}</td>
                  <td className="px-3 py-2">{e.event_type}</td>
                  <td className="px-3 py-2 font-mono text-xs">{e.actor_id ?? "—"}</td>
                  <td className="px-3 py-2">
                    <pre className="max-w-xs overflow-hidden whitespace-pre-wrap break-words text-xs text-slate-700">
{JSON.stringify(e.details)}
                    </pre>
                  </td>
                  <td className="px-3 py-2 font-mono text-xs">{e.entry_hash.slice(0, 10)}…</td>
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
          disabled={(q.data?.entries.length ?? 0) < limit}
          onClick={() => setOffset(offset + limit)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
