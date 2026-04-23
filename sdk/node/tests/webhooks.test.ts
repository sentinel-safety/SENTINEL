import { createHmac } from "node:crypto";

import { verifyWebhookSignature, WebhookSignatureError } from "../src/webhooks.js";

function sign(secret: string, timestamp: Date, body: Buffer): string {
  const ts = Math.floor(timestamp.getTime() / 1000);
  const msg = Buffer.concat([Buffer.from(`${ts}.`), body]);
  const digest = createHmac("sha256", secret).update(msg).digest("hex");
  return `t=${ts},v1=${digest}`;
}

describe("verifyWebhookSignature", () => {
  const secret = "whsec_test"; // pragma: allowlist secret
  const ts = new Date("2026-04-20T12:00:00Z");
  const body = Buffer.from('{"hello":"world"}');

  it("valid signature passes", () => {
    const header = sign(secret, ts, body);
    expect(() =>
      verifyWebhookSignature({ header, secret, body, now: ts, skewSeconds: 300 })
    ).not.toThrow();
  });

  it("malformed header fails", () => {
    expect(() =>
      verifyWebhookSignature({
        header: "garbage",
        secret,
        body,
        now: ts,
        skewSeconds: 300
      })
    ).toThrow(WebhookSignatureError);
  });

  it("tampered body fails", () => {
    const header = sign(secret, ts, body);
    expect(() =>
      verifyWebhookSignature({
        header,
        secret,
        body: Buffer.from('{"hello":"evil"}'),
        now: ts,
        skewSeconds: 300
      })
    ).toThrow(WebhookSignatureError);
  });

  it("stale timestamp fails", () => {
    const header = sign(secret, ts, body);
    const laterNow = new Date(ts.getTime() + 1000 * 1000);
    expect(() =>
      verifyWebhookSignature({ header, secret, body, now: laterNow, skewSeconds: 300 })
    ).toThrow(WebhookSignatureError);
  });

  it("future timestamp fails", () => {
    const header = sign(secret, ts, body);
    const earlierNow = new Date(ts.getTime() - 1000 * 1000);
    expect(() =>
      verifyWebhookSignature({ header, secret, body, now: earlierNow, skewSeconds: 300 })
    ).toThrow(WebhookSignatureError);
  });

  it("wrong secret fails", () => {
    const header = sign("right", ts, body);
    expect(() =>
      verifyWebhookSignature({ header, secret: "wrong", body, now: ts, skewSeconds: 300 }) // pragma: allowlist secret
    ).toThrow(WebhookSignatureError);
  });
});
