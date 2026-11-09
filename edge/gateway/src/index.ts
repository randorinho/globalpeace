/**
 * globalpeace.ai edge — the whole public surface (docs/DARK_ORIGIN.md).
 *
 * The origin accepts no inbound connections at all. This worker serves the
 * static frontend, proxies the basemap, answers /api/public/* reads from
 * published snapshots (R2), buffers the single public write (contributions)
 * in D1, and exposes gateway-secret-authenticated /api/internal/* routes
 * that the origin calls OUTBOUND to drain that buffer.
 */

const API_PREFIX = "/api";

// Basemap proxy (DPO desvio D15): glyphs and country tiles are fetched by the
// edge on the visitor's behalf so the visitor's IP and headers never reach the
// third-party tile host. The TileJSON's absolute upstream URLs are rewritten
// to this proxy, otherwise the browser would contact the upstream directly.
const MAP_PREFIX = "/map";
const MAP_UPSTREAM = "https://demotiles.maplibre.org";
const MAP_CACHE_SECONDS = 86400;

// Methods the public API accepts; everything else is rejected at the edge.
const ALLOWED_METHODS = new Set(["GET", "HEAD", "POST", "OPTIONS"]);

function jsonError(status: number, detail: string): Response {
  return Response.json({ detail }, { status });
}

// Dark-origin snapshots (docs/DARK_ORIGIN.md): maps a public GET to its
// snapshot key in the SNAPSHOTS bucket. Must mirror the publisher's table
// (pipelines/publish/run.py). Returns null for shapes that aren't snapshotted
// (those keep proxying to the origin until phase 3).
function snapshotKey(url: URL): string | null {
  const rest = url.pathname.slice(`${API_PREFIX}/public`.length);
  if (rest === "/events") return "public/events.json"; // limit param is advisory: one canonical file
  if (rest === "/events.geojson") return "public/events.geojson";
  if (rest === "/events.csv") return "public/events.csv";
  if (rest === "/arms-transfers") {
    const country = url.searchParams.get("country");
    if (!country) return "public/arms-transfers.json";
    return /^[A-Za-z]{2}$/.test(country)
      ? `public/arms-transfers/${country.toUpperCase()}.json`
      : null; // name-based lookups stay on the origin
  }
  if (rest === "/hra/position") return "public/hra/position.json";
  if (rest === "/hra/positions") return "public/hra/positions.json";
  if (rest === "/solutions") return "public/solutions.json";
  if (rest === "/solutions/history") return "public/solutions/history.json";
  if (rest === "/meta") return "public/meta.json"; // snapshot-only (no origin equivalent)
  const trail = /^\/events\/([A-Za-z0-9-]{1,64})\/trail$/.exec(rest);
  if (trail) return `public/trails/${trail[1]}.json`;
  return null;
}

const SNAPSHOT_CACHE_SECONDS = 300;

// ---- public contributions buffer (dark-origin phase 2) ---------------------
// The edge enforces what the origin enforces (backend/app/routers/public.py):
// honeypot, size caps, PII screen, 5/hour per hashed client IP. The canonical
// Python screen re-runs at drain time; this is the first gate, not the last.

const RATE_MAX = 5;
const PII_PATTERN = /\b[\w.+-]+@[\w-]+\.[\w.]+\b|\+?\d[\d\s().-]{8,}\d/;

async function clientHash(request: Request): Promise<string> {
  // Hashed, never stored raw — mirrors the origin's data minimisation.
  const ip = request.headers.get("cf-connecting-ip") ?? "?";
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(ip));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 16);
}

function secretOk(request: Request, env: Env): boolean {
  const supplied = new TextEncoder().encode(request.headers.get("x-gateway-secret") ?? "");
  const expected = new TextEncoder().encode(env.GATEWAY_SHARED_SECRET);
  return supplied.byteLength === expected.byteLength &&
    crypto.subtle.timingSafeEqual(supplied, expected);
}

async function submitContribution(request: Request, env: Env): Promise<Response> {
  let body: { text?: unknown; url?: unknown; event_id?: unknown; website?: unknown };
  try {
    body = await request.json();
  } catch {
    return jsonError(422, "invalid JSON body");
  }
  if (body.website !== undefined && body.website !== "") {
    return jsonError(422, "invalid submission"); // honeypot — never name it
  }
  const text = typeof body.text === "string" ? body.text.trim() : "";
  if (text.length < 10 || text.length > 2000) {
    return jsonError(422, "text must be between 10 and 2000 characters");
  }
  if (PII_PATTERN.test(text)) {
    return jsonError(422,
      "please remove personal data (emails, phone numbers) — testimonies are pseudonymised by design");
  }
  let contributionUrl: string | null = null;
  if (body.url !== undefined && body.url !== null && body.url !== "") {
    try {
      const parsed = new URL(String(body.url));
      if (!/^https?:$/.test(parsed.protocol) || String(body.url).length > 2048) throw new Error();
      contributionUrl = parsed.toString();
    } catch {
      return jsonError(422, "url must be a valid http(s) link");
    }
  }
  const eventId = typeof body.event_id === "string" ? body.event_id : null;
  if (eventId !== null && !/^[A-Za-z0-9-]{1,64}$/.test(eventId)) {
    return jsonError(422, "invalid event_id"); // referential check happens at drain time
  }
  const hash = await clientHash(request);
  try {
    const recent = await env.PENDING.prepare(
      "SELECT COUNT(*) AS n FROM pending_contributions WHERE client_hash = ?1 AND created_at > datetime('now', '-1 hour')",
    ).bind(hash).first<{ n: number }>();
    if ((recent?.n ?? 0) >= RATE_MAX) {
      return jsonError(429, "rate limit: try again later");
    }
    const id = crypto.randomUUID();
    await env.PENDING.prepare(
      "INSERT INTO pending_contributions (id, event_id, text, url, client_hash, created_at) VALUES (?1, ?2, ?3, ?4, ?5, datetime('now'))",
    ).bind(id, eventId, text, contributionUrl, hash).run();
    return Response.json(
      { contribution_id: id, event_id: eventId, text, url: contributionUrl, status: "pending" },
      { status: 202 },
    );
  } catch (err) {
    console.log(JSON.stringify({
      level: "error", msg: "contribution buffer write failed",
      error: err instanceof Error ? err.message : String(err),
    }));
    return jsonError(503, "contributions temporarily unavailable — try again later");
  }
}

// Origin-initiated drain (pipelines/contributions): list pending, then ack.
// Ack flags drained=1 rather than deleting so the hourly rate limit stays
// exact across drains; drained rows are purged after 25 h.
async function handleInternal(rest: string, request: Request, env: Env): Promise<Response> {
  if (!secretOk(request, env)) {
    return jsonError(403, "forbidden");
  }
  if (rest === "/internal/contributions/pending" && request.method === "GET") {
    const rows = await env.PENDING.prepare(
      "SELECT id, event_id, text, url, created_at FROM pending_contributions WHERE drained = 0 ORDER BY created_at LIMIT 200",
    ).all();
    return Response.json({ contributions: rows.results });
  }
  if (rest === "/internal/contributions/ack" && request.method === "POST") {
    const body = (await request.json().catch(() => ({}))) as { ids?: unknown };
    const ids = Array.isArray(body.ids)
      ? body.ids.filter((x): x is string => typeof x === "string").slice(0, 200)
      : [];
    let acked = 0;
    for (const id of ids) {
      const res = await env.PENDING.prepare(
        "UPDATE pending_contributions SET drained = 1 WHERE id = ?1",
      ).bind(id).run();
      acked += res.meta.changes ?? 0;
    }
    await env.PENDING.prepare(
      "DELETE FROM pending_contributions WHERE drained = 1 AND created_at < datetime('now', '-25 hours')",
    ).run();
    return Response.json({ acked });
  }
  return jsonError(404, "not found");
}

export default {
  async fetch(request, env): Promise<Response> {
    const url = new URL(request.url);

    if (!ALLOWED_METHODS.has(request.method)) {
      return jsonError(405, "method not allowed");
    }

    // Edge health check — answered without touching the origin.
    if (url.pathname === `${API_PREFIX}/edge-healthz`) {
      return Response.json({ status: "ok", edge: true });
    }

    if (url.pathname.startsWith(`${MAP_PREFIX}/`)) {
      if (request.method !== "GET" && request.method !== "HEAD") {
        return jsonError(405, "method not allowed");
      }
      const upstreamPath = url.pathname.slice(MAP_PREFIX.length);
      try {
        // Fresh request, no client headers forwarded — the tile host sees
        // only the Cloudflare egress, never the visitor.
        const upstream = await fetch(`${MAP_UPSTREAM}${upstreamPath}`, {
          method: request.method,
          cf: { cacheEverything: true, cacheTtl: MAP_CACHE_SECONDS },
        });
        const headers = new Headers(upstream.headers);
        headers.set("cache-control", `public, max-age=${MAP_CACHE_SECONDS}`);
        if (upstreamPath === "/tiles/tiles.json") {
          const tilejson = (await upstream.text()).replaceAll(
            MAP_UPSTREAM,
            `${url.origin}${MAP_PREFIX}`,
          );
          headers.set("content-type", "application/json");
          return new Response(tilejson, { status: upstream.status, headers });
        }
        return new Response(upstream.body, { status: upstream.status, headers });
      } catch (err) {
        console.log(
          JSON.stringify({
            level: "error",
            msg: "map upstream fetch failed",
            path: url.pathname,
            error: err instanceof Error ? err.message : String(err),
          }),
        );
        return jsonError(502, "map tiles unavailable");
      }
    }

    if (!url.pathname.startsWith(API_PREFIX)) {
      // Asset misses land here. Browsers were already caught by the asset
      // layer's SPA fallback; non-navigation clients (crawlers following
      // sitemap.xml's canonical path urls) get the same shell — main.tsx
      // translates the path to the matching hash route.
      if (request.method === "GET" || request.method === "HEAD") {
        return env.ASSETS.fetch(new Request(`${url.origin}/`, { method: request.method }));
      }
      return jsonError(404, "not found");
    }

    // Only reviewed-data endpoints are public. Review, ingestion, audit and
    // evidence APIs stay closed at the edge until a Cloudflare Access policy
    // protects them — reviewers work via the local dashboard meanwhile.
    const rest = url.pathname.slice(API_PREFIX.length) || "/";

    // Origin-initiated drain of the contributions buffer (shared-secret auth).
    if (rest.startsWith("/internal/")) {
      return handleInternal(rest, request, env);
    }

    // Dark origin, phase 3 (docs/DARK_ORIGIN.md): there is NO path from here
    // to the origin. Public reads are published snapshots; the only write is
    // the D1 contributions buffer; everything else ends at the edge.
    if (!rest.startsWith("/public/")) {
      return jsonError(403, "this endpoint requires authenticated access");
    }

    // Contributions never travel to the origin: buffered in D1 at the edge,
    // drained by the origin during pipeline windows (dark-origin phase 2).
    if (rest === "/public/contributions" && request.method === "POST") {
      return submitContribution(request, env);
    }

    if (request.method !== "GET" && request.method !== "HEAD") {
      return jsonError(405, "method not allowed");
    }
    const key = snapshotKey(url);
    if (!key) {
      return jsonError(404, "not found");
    }
    const object = await env.SNAPSHOTS.get(key);
    if (!object) {
      // Absent per-country arms file means "no documented transfers", not an
      // error — the publisher only emits countries with data.
      if (/^public\/arms-transfers\/[A-Z]{2}\.json$/.test(key)) {
        return Response.json(
          {
            attribution: "Source: SIPRI Arms Transfers Database (where source=SIPRI); "
              + "TIV values are SIPRI trend-indicator values, not prices.",
            count: 0,
            transfers: [],
          },
          { headers: { "cache-control": `public, max-age=${SNAPSHOT_CACHE_SECONDS}` } },
        );
      }
      return jsonError(404, "not found");
    }
    const headers = new Headers({
      "content-type": object.httpMetadata?.contentType ?? "application/json",
      "cache-control": `public, max-age=${SNAPSHOT_CACHE_SECONDS}`,
      etag: object.httpEtag,
      "x-gpai-snapshot": "1",
    });
    if (key === "public/events.csv") {
      headers.set("content-disposition", 'attachment; filename="globalpeace-events.csv"');
    }
    return new Response(request.method === "HEAD" ? null : object.body, { headers });
  },
} satisfies ExportedHandler<Env>;
