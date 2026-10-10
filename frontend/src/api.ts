import type { GPEvent, ReviewDecision, ReviewRecord } from "./types";

const BASE = "/api";

async function check(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ? JSON.stringify(body.detail) : `HTTP ${res.status}`);
  }
  return res;
}

export async function fetchQueue(params: { country?: string; event_type?: string }) {
  const q = new URLSearchParams({ limit: "200" });
  if (params.country) q.set("country", params.country);
  if (params.event_type) q.set("event_type", params.event_type);
  const res = await check(await fetch(`${BASE}/review/queue?${q}`));
  return (await res.json()) as { pending: number; events: GPEvent[] };
}

export async function fetchHistory(eventId: string) {
  const res = await check(await fetch(`${BASE}/events/${eventId}/history`));
  return (await res.json()) as ReviewRecord[];
}

export async function postReview(eventId: string, reviewer: string, decision: ReviewDecision) {
  const res = await check(
    await fetch(`${BASE}/events/${eventId}/review`, {
      method: "POST",
      headers: { "content-type": "application/json", "x-reviewer": reviewer },
      body: JSON.stringify(decision),
    }),
  );
  return (await res.json()) as ReviewRecord;
}
