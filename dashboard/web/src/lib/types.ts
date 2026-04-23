// Copyright 2026 Sentinel Foundation. All Rights Reserved.
//
// Licensed under the SENTINEL License Agreement. See LICENSE file in the project
// root for full terms.


import type { DashboardRole } from "./roles";

export interface SessionUser {
  id: string;
  tenant_id: string;
  email: string;
  role: DashboardRole;
  display_name: string;
  last_login_at?: string | null;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: SessionUser;
}

export interface RefreshResponse {
  access_token: string;
}

export interface AlertListItem {
  actor_id: string;
  current_score: number;
  tier: number;
  tier_entered_at: string;
  last_updated: string;
  claimed_age_band: string;
}

export interface AlertListResponse {
  alerts: AlertListItem[];
}

export interface ActorDetail {
  actor_id: string;
  tenant_id: string;
  claimed_age_band: string;
  account_created_at: string | null;
  current_score: number | null;
  tier: number | null;
  tier_entered_at: string | null;
}

export interface EventSummary {
  id: string;
  conversation_id: string;
  timestamp: string;
  type: string;
  score_delta: number;
}

export interface EventListResponse {
  events: EventSummary[];
}

export interface ReasoningEntry {
  id: string;
  event_id: string | null;
  reasoning_json: Record<string, unknown>;
  created_at: string;
}

export interface ReasoningListResponse {
  reasoning: ReasoningEntry[];
}

export interface InvestigationMessage {
  event_id: string;
  actor_id: string;
  timestamp: string;
  type: string;
  content_features: Record<string, unknown>;
}

export interface InvestigationMessagesResponse {
  messages: InvestigationMessage[];
}

export interface AuditEntryItem {
  id: string;
  sequence: number;
  actor_id: string | null;
  event_type: string;
  details: Record<string, unknown>;
  timestamp: string;
  entry_hash: string;
}

export interface AuditEntryListResponse {
  entries: AuditEntryItem[];
}

export interface BiasGroupRow {
  group: string;
  total_actors: number;
  total_flagged: number;
  flag_rate: number;
}

export interface BiasAuditResponse {
  group_by: string;
  rows: BiasGroupRow[];
}

export interface ComplianceExportRequest {
  from: string;
  to: string;
  categories: string[];
  format: "zip";
}

export interface TenantSettings {
  name: string;
  tier: string;
  compliance_jurisdictions: string[];
  data_retention_days: number;
}

export interface TenantActionConfigResponse {
  mode: "advisory" | "auto_enforce";
  action_overrides: Record<string, string[]>;
}

export interface WebhookListItem {
  id: string;
  url: string;
  events: string[];
  active: boolean;
  created_at: string;
}

export interface WebhookListResponse {
  webhooks: WebhookListItem[];
}

export interface WebhookCreateRequest {
  url: string;
  events: string[];
}

export interface WebhookCreateResponse {
  webhook: WebhookListItem;
  secret: string;
}

export interface ApiKeySummary {
  id: string;
  name: string;
  prefix: string;
  scope: string;
  created_at: string;
  revoked_at: string | null;
  last_used_at: string | null;
}

export interface ApiKeyListResponse {
  api_keys: ApiKeySummary[];
}

export interface ApiKeyCreateRequest {
  name: string;
  scope: "read" | "write" | "admin";
}

export interface ApiKeyCreateResponse {
  api_key: ApiKeySummary;
  secret: string;
}
