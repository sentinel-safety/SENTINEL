// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


export type DashboardRole = "admin" | "mod" | "viewer" | "auditor";

export const ALL_ROLES: readonly DashboardRole[] = ["admin", "mod", "viewer", "auditor"] as const;

export function hasAnyRole(role: DashboardRole, allow: readonly DashboardRole[]): boolean {
  return allow.includes(role);
}
