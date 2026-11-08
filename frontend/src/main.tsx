import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";

// Canonical path URLs (sitemap.xml, external links) land here via the SPA
// fallback; the router is hash-based, so translate /about → /#/about before
// the app reads location.hash.
const { pathname, hash } = window.location;
if (pathname !== "/" && !hash) {
  window.history.replaceState(null, "", `/#${pathname}`);
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
