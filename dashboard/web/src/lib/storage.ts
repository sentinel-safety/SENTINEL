// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


import type { SessionUser } from "./types";

const SESSION_KEY = "sentinel_session";

export interface StoredSession {
  access_token: string;
  refresh_token: string;
  user: SessionUser;
}

export function readSession(): StoredSession | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredSession;
  } catch {
    return null;
  }
}

export function writeSession(session: StoredSession): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(SESSION_KEY);
}

export function updateAccessToken(newAccess: string): void {
  const s = readSession();
  if (!s) return;
  writeSession({ ...s, access_token: newAccess });
}
