// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


import type { DashboardRole } from "./roles";

export interface NavItem {
  label: string;
  href: string;
  allow: readonly DashboardRole[];
}

export const NAV_ITEMS: readonly NavItem[] = [
  { label: "Alerts", href: "/alerts", allow: ["admin", "mod", "auditor"] },
  { label: "Audit log", href: "/audit-log", allow: ["admin", "auditor"] },
  { label: "Compliance", href: "/compliance", allow: ["admin", "auditor"] },
  { label: "Bias audit", href: "/bias-audit", allow: ["admin", "auditor"] },
  { label: "Settings", href: "/settings", allow: ["admin"] },
] as const;
