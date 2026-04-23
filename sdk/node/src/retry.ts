export function computeBackoff(attempt: number, base: number, cap: number): number {
  if (attempt < 1) {
    throw new RangeError("attempt must be >= 1");
  }
  return Math.min(cap, base * 2 ** (attempt - 1));
}

export function parseRetryAfter(value: string | null, now: Date): number | null {
  if (value === null) {
    return null;
  }
  const trimmed = value.trim();
  if (trimmed.length === 0) {
    return null;
  }
  if (/^-?\d+(?:\.\d+)?$/.test(trimmed)) {
    const asNumber = Number(trimmed);
    return Math.max(0, asNumber);
  }
  const asDate = new Date(trimmed);
  if (Number.isNaN(asDate.getTime())) {
    return null;
  }
  const deltaSeconds = (asDate.getTime() - now.getTime()) / 1000;
  return Math.max(0, deltaSeconds);
}
