import {
  AuthError,
  RateLimitError,
  SentinelError,
  ServerError,
  TimeoutError
} from "../src/errors.js";

describe("errors", () => {
  it("AuthError inherits from SentinelError", () => {
    const e = new AuthError("bad key");
    expect(e).toBeInstanceOf(SentinelError);
    expect(e.message).toBe("bad key");
    expect(e.name).toBe("AuthError");
  });

  it("RateLimitError carries retry-after", () => {
    const e = new RateLimitError("slow", 42);
    expect(e.retryAfterSeconds).toBe(42);
  });

  it("ServerError carries status code", () => {
    const e = new ServerError("boom", 503);
    expect(e.statusCode).toBe(503);
  });

  it("TimeoutError inherits from SentinelError", () => {
    expect(new TimeoutError("x")).toBeInstanceOf(SentinelError);
  });
});
