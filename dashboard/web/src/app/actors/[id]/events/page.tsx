// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { use } from "react";
import { EventsList } from "@/components/events-list";

export default function ActorEventsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return <EventsList actorId={id} />;
}
