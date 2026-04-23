// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


import { BFF_BASE_URL } from "./env";
import { clearSession, readSession, updateAccessToken } from "./storage";

export class ApiError extends Error {
  status: number;
  bodyText: string;

  constructor(status: number, bodyText: string) {
    super(`ApiError ${status}: ${bodyText}`);
    this.status = status;
    this.bodyText = bodyText;
  }
}

export interface ApiFetchOptions extends RequestInit {
  asBlob?: boolean;
  extraHeaders?: Record<string, string>;
  _retried?: boolean;
}

async function refreshAccess(): Promise<string | null> {
  const session = readSession();
  if (!session) return null;
  const res = await fetch(`${BFF_BASE_URL}/dashboard/api/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: session.refresh_token }),
  });
  if (!res.ok) return null;
  const body = (await res.json()) as { access_token: string };
  updateAccessToken(body.access_token);
  return body.access_token;
}

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {}
): Promise<T> {
  const session = readSession();
  const headers = new Headers(options.headers ?? {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData) && options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (session) {
    headers.set("Authorization", `Bearer ${session.access_token}`);
  }
  if (options.extraHeaders) {
    for (const [k, v] of Object.entries(options.extraHeaders)) {
      headers.set(k, v);
    }
  }
  const res = await fetch(`${BFF_BASE_URL}${path}`, { ...options, headers });
  if (res.status === 401 && !options._retried) {
    const newAccess = await refreshAccess();
    if (newAccess) {
      return apiFetch<T>(path, { ...options, _retried: true });
    }
    clearSession();
    throw new ApiError(401, await safeText(res));
  }
  if (!res.ok) {
    throw new ApiError(res.status, await safeText(res));
  }
  if (options.asBlob) {
    return (await res.blob()) as unknown as T;
  }
  if (res.status === 204) {
    return undefined as unknown as T;
  }
  const ct = res.headers.get("Content-Type") ?? "";
  if (ct.includes("application/json")) {
    return (await res.json()) as T;
  }
  return (await res.text()) as unknown as T;
}

async function safeText(res: Response): Promise<string> {
  try {
    return await res.text();
  } catch {
    return "";
  }
}
