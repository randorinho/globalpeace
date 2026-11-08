/**
 * globalpeace.ai API gateway.
 *
 * Public edge entrypoint for /api/*. Proxies to the FastAPI origin through
 * Cloudflare Tunnel, attaching the gateway shared secret (and Cloudflare
 * Access service-token headers when the tunnel is Access-protected).
 *
 * Responses are streamed through — request/response bodies are never buffered.
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
    if (!rest.startsWith("/public/") && rest !== "/healthz") {
      return jsonError(403, "this endpoint requires authenticated access");
    }

    // Public GETs serve from the published snapshot when one exists; a miss
    // falls through to the origin proxy (phase-1 reversibility).
    if (request.method === "GET" && rest.startsWith("/public/")) {
      const key = snapshotKey(url);
      const object = key ? await env.SNAPSHOTS.get(key) : null;
      if (object) {
        const headers = new Headers({
          "content-type": object.httpMetadata?.contentType ?? "application/json",
          "cache-control": `public, max-age=${SNAPSHOT_CACHE_SECONDS}`,
          etag: object.httpEtag,
          "x-gpai-snapshot": "1",
        });
        if (key === "public/events.csv") {
          headers.set("content-disposition", 'attachment; filename="globalpeace-events.csv"');
        }
        return new Response(object.body, { headers });
      }
    }

    // Map /api/<rest> → origin /<rest>
    const originUrl = new URL(env.ORIGIN_URL);
    originUrl.pathname = url.pathname.slice(API_PREFIX.length) || "/";
    originUrl.search = url.search;

    const headers = new Headers(request.headers);
    headers.set("x-gateway-secret", env.GATEWAY_SHARED_SECRET);
    if (env.CF_ACCESS_CLIENT_ID && env.CF_ACCESS_CLIENT_SECRET) {
      headers.set("CF-Access-Client-Id", env.CF_ACCESS_CLIENT_ID);
      headers.set("CF-Access-Client-Secret", env.CF_ACCESS_CLIENT_SECRET);
    }

    try {
      // Body streams through untouched; the Response is returned as-is so the
      // origin's stream is piped to the client without buffering.
      const originResponse = await fetch(originUrl, {
        method: request.method,
        headers,
        body: request.body,
      });

      // Strip the shared secret from any echo/debug paths; copy headers so we
      // can adjust without mutating the immutable origin response.
      const responseHeaders = new Headers(originResponse.headers);
      responseHeaders.delete("x-gateway-secret");

      return new Response(originResponse.body, {
        status: originResponse.status,
        statusText: originResponse.statusText,
        headers: responseHeaders,
      });
    } catch (err) {
      console.log(
        JSON.stringify({
          level: "error",
          msg: "origin fetch failed",
          path: url.pathname,
          error: err instanceof Error ? err.message : String(err),
        }),
      );
      return jsonError(502, "origin unavailable");
    }
  },
} satisfies ExportedHandler<Env>;
