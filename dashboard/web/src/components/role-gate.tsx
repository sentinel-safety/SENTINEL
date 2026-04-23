// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


"use client";

import type { ReactNode } from "react";
import { useAuth } from "@/lib/auth-context";
import type { DashboardRole } from "@/lib/roles";
import { hasAnyRole } from "@/lib/roles";

interface Props {
  allow: readonly DashboardRole[];
  fallback?: ReactNode;
  children: ReactNode;
}

export function RoleGate({ allow, fallback = null, children }: Props) {
  const { user } = useAuth();
  if (!user) return <>{fallback}</>;
  if (!hasAnyRole(user.role, allow)) return <>{fallback}</>;
  return <>{children}</>;
}
