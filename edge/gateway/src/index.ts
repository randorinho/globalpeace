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

    if (!url.pathname.startsWith(API_PREFIX)) {
      return jsonError(404, "not found");
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
