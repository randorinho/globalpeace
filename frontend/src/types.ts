export type VerificationStatus =
  | "unverified" | "partially_verified" | "verified" | "disputed" | "retracted";
export type EventType = "protest" | "attack" | "negotiation" | "displacement";

export interface AIAudit {
  verdict: "credible_recent" | "needs_additional_verification" | "stale_low_priority";
  score: number;
  signals: Record<string, unknown>;
  reasons: string[];
  cross_checks: Record<string, string>;
  llm_opinion: Record<string, unknown> | null;
  engine: string;
  human_review_required: boolean;
  audited_at: string;
}

export interface EvidenceItem {
  evidence_id: string;
  event_id: string;
  submitted_by: string;
  url: string;
  direction: "supports" | "contradicts" | "context";
  note: string;
  source_tier: string;
  reachable: boolean;
  covers_cross_check: string | null;
  created_at: string;
}

export interface EvidenceSummary {
  supports: number;
  contradicts: number;
  context: number;
  distinct_domains: number;
  cross_checks_covered: string[];
  ready_for_rereview: boolean;
}

export interface GPEvent {
  event_id: string;
  title: string;
  ai_audit: AIAudit | null;
  date_time: string;
  location: { lat: number; lon: number } | null;
  country: string;
  actors: string[];
  event_type: EventType;
  information_type: string;
  source_urls: string[];
  source_language: string;
  confidence: number;
  verification_status: VerificationStatus;
  civilian_impact: Record<string, unknown>;
  human_review: boolean;
  last_updated: string;
}

export interface ReviewRecord {
  review_id: string;
  event_id: string;
  reviewer: string;
  previous_status: VerificationStatus;
  new_status: VerificationStatus;
  note: string;
  sources_consulted: string[];
  changes: Record<string, { from: unknown; to: unknown }>;
  created_at: string;
}

export interface ReviewDecision {
  status: VerificationStatus;
  note: string;
  sources_consulted: string[];
  corrections?: { country?: string; event_type?: EventType; confidence?: number };
}
