import { createHmac, timingSafeEqual } from "node:crypto";

export class WebhookSignatureError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "WebhookSignatureError";
  }
}

export interface VerifyWebhookSignatureOptions {
  header: string;
  secret: string;
  body: Buffer | Uint8Array | string;
  now: Date;
  skewSeconds?: number;
}

function parseHeader(header: string): { t: number; v1: string } {
  const parts = header.split(",").reduce<Record<string, string>>((acc, item) => {
    const eq = item.indexOf("=");
    if (eq > 0) {
      acc[item.slice(0, eq).trim()] = item.slice(eq + 1).trim();
    }
    return acc;
  }, {});
  const tRaw = parts.t;
  const v1 = parts.v1;
  if (!tRaw || !v1) {
    throw new WebhookSignatureError("malformed signature header");
  }
  const t = Number(tRaw);
  if (!Number.isFinite(t)) {
    throw new WebhookSignatureError("invalid timestamp");
  }
  return { t, v1 };
}

function toBuffer(body: Buffer | Uint8Array | string): Buffer {
  if (Buffer.isBuffer(body)) {
    return body;
  }
  if (typeof body === "string") {
    return Buffer.from(body);
  }
  return Buffer.from(body);
}

export function verifyWebhookSignature(options: VerifyWebhookSignatureOptions): void {
  const skew = options.skewSeconds ?? 300;
  const { t, v1 } = parseHeader(options.header);
  const nowSeconds = Math.floor(options.now.getTime() / 1000);
  if (Math.abs(nowSeconds - t) > skew) {
    throw new WebhookSignatureError("timestamp outside allowed skew");
  }
  const buffer = toBuffer(options.body);
  const message = Buffer.concat([Buffer.from(`${t}.`), buffer]);
  const expected = createHmac("sha256", options.secret).update(message).digest("hex");
  const expectedBuf = Buffer.from(expected, "utf8");
  const providedBuf = Buffer.from(v1, "utf8");
  if (expectedBuf.length !== providedBuf.length || !timingSafeEqual(expectedBuf, providedBuf)) {
    throw new WebhookSignatureError("signature mismatch");
  }
}
