// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { use } from "react";
import { InvestigationMessages } from "@/components/investigation-messages";
import { Shell } from "@/components/shell";
import { RoleGate } from "@/components/role-gate";

export default function InvestigationPage({
  params,
}: {
  params: Promise<{ id: string; conversationId: string }>;
}) {
  const { conversationId } = use(params);
  return (
    <Shell>
      <h1 className="mb-4 text-xl font-semibold">Investigation workspace</h1>
      <RoleGate
        allow={["admin", "mod"]}
        fallback={<div className="text-sm text-slate-600">Only admins and moderators may view conversation content.</div>}
      >
        <InvestigationMessages conversationId={conversationId} />
      </RoleGate>
    </Shell>
  );
}
