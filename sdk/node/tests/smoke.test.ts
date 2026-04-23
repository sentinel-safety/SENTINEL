import { version } from "../src/index.js";

describe("sdk metadata", () => {
  it("exposes a semver-like version", () => {
    const parts = version.split(".");
    expect(parts).toHaveLength(3);
    parts.forEach((p) => expect(p).toMatch(/^\d+$/));
  });
});
