// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function ActorTabNav({ actorId }: { actorId: string }) {
  const pathname = usePathname();
  const tabs = [
    { label: "Overview", href: `/actors/${actorId}` },
    { label: "Events", href: `/actors/${actorId}/events` },
    { label: "Reasoning", href: `/actors/${actorId}/reasoning` },
  ];
  return (
    <nav className="flex gap-2 border-b border-slate-200">
      {tabs.map((tab) => {
        const active = pathname === tab.href;
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`border-b-2 px-3 py-2 text-sm ${active ? "border-slate-900 text-slate-900" : "border-transparent text-slate-500 hover:text-slate-700"}`}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
