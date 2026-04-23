// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { Shell } from "@/components/shell";
import { AlertsTable } from "@/components/alerts-table";
import { RoleGate } from "@/components/role-gate";

export default function AlertsPage() {
  return (
    <Shell>
      <h1 className="mb-4 text-xl font-semibold">Alert queue</h1>
      <RoleGate
        allow={["admin", "mod", "auditor"]}
        fallback={<div className="text-sm text-slate-600">You don&apos;t have access to alerts.</div>}
      >
        <AlertsTable />
      </RoleGate>
    </Shell>
  );
}
