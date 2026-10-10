import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// /api/<rest> → origin /<rest>, mirroring the Workers gateway (edge/gateway).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
