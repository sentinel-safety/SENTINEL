import { computeBackoff, parseRetryAfter } from "../src/retry.js";

describe("retry helpers", () => {
  it("backoff doubles and caps", () => {
    expect(computeBackoff(1, 0.5, 8)).toBeCloseTo(0.5);
    expect(computeBackoff(2, 0.5, 8)).toBeCloseTo(1.0);
    expect(computeBackoff(3, 0.5, 8)).toBeCloseTo(2.0);
    expect(computeBackoff(4, 0.5, 8)).toBeCloseTo(4.0);
    expect(computeBackoff(10, 0.5, 8)).toBeCloseTo(8.0);
  });

  it("rejects non-positive attempt", () => {
    expect(() => computeBackoff(0, 1, 4)).toThrow(RangeError);
  });

  it("parses numeric retry-after", () => {
    expect(parseRetryAfter("7", new Date())).toBeCloseTo(7);
  });

  it("parses HTTP date retry-after", () => {
    const now = new Date("2026-04-20T12:00:00Z");
    const value = parseRetryAfter("Mon, 20 Apr 2026 12:00:30 GMT", now);
    expect(value).not.toBeNull();
    expect(Math.abs((value ?? 0) - 30)).toBeLessThan(1);
  });

  it("returns null for invalid values", () => {
    expect(parseRetryAfter("banana", new Date())).toBeNull();
    expect(parseRetryAfter(null, new Date())).toBeNull();
  });

  it("clamps negative numeric retry-after to zero", () => {
    expect(parseRetryAfter("-7", new Date())).toBe(0);
  });
});
