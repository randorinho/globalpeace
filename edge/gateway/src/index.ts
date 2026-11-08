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
