export enum EventType {
  Message = "message",
  Image = "image",
  FriendRequest = "friend_request",
  Gift = "gift",
  ProfileChange = "profile_change",
  VoiceClip = "voice_clip"
}

export enum ResponseTier {
  Trusted = "trusted",
  Watch = "watch",
  ActiveMonitor = "active_monitor",
  Throttle = "throttle",
  Restrict = "restrict",
  Critical = "critical"
}

export enum ActionKind {
  None = "none",
  SilentLog = "silent_log",
  ReviewQueue = "review_queue",
  ThrottleDmToMinors = "throttle_dm_to_minors",
  DisableMediaToMinors = "disable_media_to_minors",
  RequireApprovalToFriendMinor = "require_approval_to_friend_minor",
  RestrictToPublicPosts = "restrict_to_public_posts",
  BlockDmToMinors = "block_dm_to_minors",
  AccountWarning = "account_warning",
  Suspend = "suspend",
  MandatoryReport = "mandatory_report"
}

export interface PrimaryDriver {
  pattern: string;
  patternId: string;
  confidence: number;
  evidence: string;
}

export interface RecommendedAction {
  kind: ActionKind;
  description: string;
  parameters: Record<string, unknown>;
}

export interface Reasoning {
  actorId: string;
  tenantId: string;
  scoreChange: number;
  newScore: number;
  newTier: ResponseTier;
  primaryDrivers: readonly PrimaryDriver[];
  context: string;
  recommendedActionSummary: string;
  generatedAt: string;
  nextReviewAt: string | null;
}

export interface ScoreResult {
  currentScore: number;
  previousScore: number;
  delta: number;
  tier: ResponseTier;
  reasoning: Reasoning | null;
}

export interface MessageEventInput {
  tenantId: string;
  conversationId: string;
  actorExternalIdHash: string;
  content: string;
  timestamp: Date;
  eventType?: EventType;
  targetActorExternalIdHashes?: readonly string[];
  metadata?: Record<string, unknown>;
  idempotencyKey?: string;
}
