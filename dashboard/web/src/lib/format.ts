// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


export function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toISOString().replace("T", " ").slice(0, 19) + " UTC";
}

export function formatTier(tier: number | null | undefined): string {
  if (tier === null || tier === undefined) return "—";
  return `T${tier}`;
}

export function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined) return "—";
  return String(score);
}

export function formatPercent(n: number): string {
  return `${(n * 100).toFixed(2)}%`;
}
