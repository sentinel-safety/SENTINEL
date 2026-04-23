// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Button } from "./button";

export function Header() {
  const { user, logout } = useAuth();
  const router = useRouter();
  if (!user) return null;

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3">
      <div className="text-base font-semibold text-slate-900">SENTINEL</div>
      <div className="flex items-center gap-3 text-sm">
        <span className="text-slate-600">
          {user.email} <span className="rounded bg-slate-100 px-2 py-0.5 text-xs uppercase">{user.role}</span>
        </span>
        <Button variant="secondary" onClick={handleLogout}>
          Sign out
        </Button>
      </div>
    </header>
  );
}
