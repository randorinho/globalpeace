import fs from "node:fs";
import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

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
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
        headers: { "x-gateway-secret": gatewaySecret() },
      },
    },
  },
});
