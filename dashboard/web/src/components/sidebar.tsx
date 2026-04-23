// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { hasAnyRole } from "@/lib/roles";
import { NAV_ITEMS } from "@/lib/nav-items";

export function Sidebar() {
  const { user } = useAuth();
  const pathname = usePathname();
  if (!user) return null;
  const items = NAV_ITEMS.filter((i) => hasAnyRole(user.role, i.allow));
  return (
    <nav aria-label="Main navigation" className="flex w-48 flex-col gap-1 border-r border-slate-200 bg-white p-3">
      {items.map((item) => {
        const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`rounded px-3 py-2 text-sm ${active ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"}`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
