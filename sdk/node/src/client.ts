import { EventsAPI } from "./events.js";

export interface SentinelClientOptions {
  apiKey: string;
  baseUrl: string;
  timeoutMs?: number;
  retryAttempts?: number;
  retryBaseSeconds?: number;
  retryCapSeconds?: number;
  fetchImpl?: typeof fetch;
  logger?: { warn: (msg: string) => void };
}

const DEFAULT_TIMEOUT_MS = 10000;
const DEFAULT_RETRY_ATTEMPTS = 3;
const DEFAULT_RETRY_BASE_SECONDS = 0.5;
const DEFAULT_RETRY_CAP_SECONDS = 30;
const SDK_VERSION = "0.1.0";

export class SentinelClient {
  readonly events: EventsAPI;

  constructor(options: SentinelClientOptions) {
    if (!options.apiKey) {
      throw new Error("apiKey is required");
    }
    if (!options.baseUrl) {
      throw new Error("baseUrl is required");
    }
    const baseUrl = options.baseUrl.replace(/\/+$/, "");
    this.events = new EventsAPI({
      baseUrl,
      apiKey: options.apiKey,
      userAgent: `sentinel-node/${SDK_VERSION}`,
      timeoutMs: options.timeoutMs ?? DEFAULT_TIMEOUT_MS,
      retryAttempts: options.retryAttempts ?? DEFAULT_RETRY_ATTEMPTS,
      retryBaseSeconds: options.retryBaseSeconds ?? DEFAULT_RETRY_BASE_SECONDS,
      retryCapSeconds: options.retryCapSeconds ?? DEFAULT_RETRY_CAP_SECONDS,
      fetchImpl: options.fetchImpl ?? ((url, init) => fetch(url, init)),
      logger: options.logger ?? { warn: (msg) => console.warn(msg) }
    });
  }
}
