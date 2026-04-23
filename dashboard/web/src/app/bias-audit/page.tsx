// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { BiasAuditTable } from "@/components/bias-audit-table";
import { RoleGate } from "@/components/role-gate";
import { Shell } from "@/components/shell";

export default function BiasAuditPage() {
  return (
    <Shell>
      <h1 className="mb-4 text-xl font-semibold">Bias audit</h1>
      <RoleGate
        allow={["admin", "auditor"]}
        fallback={<div className="text-sm text-slate-600">Only admins and auditors may view bias audit.</div>}
      >
        <BiasAuditTable />
      </RoleGate>
    </Shell>
  );
}
