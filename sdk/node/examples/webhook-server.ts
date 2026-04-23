import { createServer, IncomingMessage, ServerResponse } from "node:http";

import { verifyWebhookSignature, WebhookSignatureError } from "../src/index.js";

async function readBody(req: IncomingMessage): Promise<Buffer> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks);
}

async function handle(req: IncomingMessage, res: ServerResponse): Promise<void> {
  const secret = process.env.SENTINEL_WEBHOOK_SECRET;
  if (!secret) {
    res.statusCode = 500;
    res.end("secret not configured");
    return;
  }
  const header = req.headers["x-sentinel-signature"];
  if (typeof header !== "string") {
    res.statusCode = 400;
    res.end("missing signature");
    return;
  }
  const body = await readBody(req);
  try {
    verifyWebhookSignature({
      header,
      secret,
      body,
      now: new Date(),
      skewSeconds: 300
    });
  } catch (err) {
    if (err instanceof WebhookSignatureError) {
      res.statusCode = 401;
      res.end(err.message);
      return;
    }
    res.statusCode = 500;
    res.end("verification error");
    return;
  }
  res.statusCode = 200;
  res.end('{"status":"ok"}');
}

const port = Number(process.env.PORT ?? 8080);
createServer((req, res) => {
  handle(req, res).catch((err) => {
    console.error(err);
    res.statusCode = 500;
    res.end("error");
  });
}).listen(port, () => {
  console.log(`webhook server listening on :${port}`);
});
