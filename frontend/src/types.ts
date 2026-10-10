export type VerificationStatus =
  | "unverified" | "partially_verified" | "verified" | "disputed" | "retracted";
export type EventType = "protest" | "attack" | "negotiation" | "displacement";

export interface GPEvent {
  event_id: string;
  title: string;
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
