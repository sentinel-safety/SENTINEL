// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { use, type ReactNode } from "react";
import { Shell } from "@/components/shell";
import { ActorTabNav } from "@/components/actor-tab-nav";
import { RoleGate } from "@/components/role-gate";

export default function ActorLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return (
    <Shell>
      <h1 className="mb-2 text-xl font-semibold">Actor {id}</h1>
      <RoleGate
        allow={["admin", "mod", "auditor"]}
        fallback={<div className="text-sm text-slate-600">You don&apos;t have access to actors.</div>}
      >
        <ActorTabNav actorId={id} />
        <div className="mt-4">{children}</div>
      </RoleGate>
    </Shell>
  );
}
