import fs from "node:fs";
import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

import { CENTROIDS } from "./src/centroids";

// Sitemap (https://www.sitemaps.org/protocol.html), regenerated on every
// build so route or country changes propagate without a hand-kept file.
// Entries are canonical PATH urls (/about, /country/SD, …): the worker's SPA
// fallback answers them 200 and main.tsx translates them to hash routes.
// /review is deliberately absent — it's the moderation surface, not content.
const SITE = "https://globalpeace.ai";
const STATIC_ROUTES = ["/", "/proposals", "/about", "/funding", "/privacy"];

function sitemap(): Plugin {
  return {
    name: "gpai-sitemap",
    apply: "build",
    generateBundle() {
      const countries = Object.keys(CENTROIDS)
        .filter((k) => /^[A-Z]{2}$/.test(k)) // centroid table also keys name spellings
        .sort();
      const routes = [...STATIC_ROUTES, ...countries.map((c) => `/country/${c}`)];
      const source = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ...routes.map((r) => `  <url><loc>${SITE}${r}</loc></url>`),
        "</urlset>",
        "",
      ].join("\n");
      this.emitFile({ type: "asset", fileName: "sitemap.xml", source });
    },
  };
}

// The origin enforces the gateway shared secret in production mode; the local
// dev proxy injects it (read from infra/.env, gitignored) so the dashboard
// keeps working without going through the public edge.
function gatewaySecret(): string {
  if (process.env.GPAI_GATEWAY_SHARED_SECRET) return process.env.GPAI_GATEWAY_SHARED_SECRET;
  try {
    const env = fs.readFileSync(path.resolve(__dirname, "../infra/.env"), "utf8");
    return /GPAI_GATEWAY_SHARED_SECRET=(.+)/.exec(env)?.[1]?.trim() ?? "";
  } catch {
    return "";
  }
}

// /api/<rest> → origin /<rest>, mirroring the Workers gateway (edge/gateway).
export default defineConfig({
  plugins: [react(), sitemap()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
        headers: { "x-gateway-secret": gatewaySecret() },
      },
      // Basemap proxy, mirroring the Workers gateway /map route. Dev-only
      // caveat: the TileJSON body still points at the upstream host, so the
      // dev browser fetches tiles directly; production rewrites it at the edge.
      "/map": {
        target: "https://demotiles.maplibre.org",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/map/, ""),
      },
    },
  },
});
