// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { use } from "react";
import { ReasoningList } from "@/components/reasoning-list";

export default function ActorReasoningPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return <ReasoningList actorId={id} />;
}
