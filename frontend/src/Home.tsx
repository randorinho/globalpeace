import * as maplibregl from "maplibre-gl";
// maplibre-gl v6 loads its worker as a separate module; under Vite the default
// URL resolution fails ("Worker failed to load") — point it at the bundled file.
import maplibreWorkerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef, useState } from "react";
import { centroidFor } from "./centroids";
import type { GPEvent } from "./types";

maplibregl.setWorkerUrl(maplibreWorkerUrl);

const COUNTRY_NAMES = new Intl.DisplayNames(["en"], { type: "region" });
const fmt = (iso: string) => iso.slice(0, 10);

// Treatment colors — same tokens as the review dashboard badges.
const STATUS_COLOR: Record<string, string> = {
  verified: "#2B8C72",
  partially_verified: "#63CDA3",
  ai_corroborated: "#41484C", // machine-corroborated — labeled, visually distinct from human-reviewed greens
};

interface Transfer {
  supplier: string;
  recipient: string;
  designation?: string;
  delivery_year?: string;
  source?: string;
  [k: string]: unknown;
}

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/** Deterministic jitter so same-country events spread around the centroid
 *  without implying precision we don't have. */
function jitter(id: string): [number, number] {
  let h = 0;
  for (const c of id) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  const angle = (h % 360) * (Math.PI / 180);
  const dist = 0.4 + ((h >>> 8) % 100) / 100;
  return [Math.cos(angle) * dist, Math.sin(angle) * dist * 0.7];
}

function impactBump(ev: GPEvent): number {
  const total = Object.values(ev.civilian_impact ?? {}).reduce<number>(
    (acc, v) => acc + (typeof v === "number" ? v : 0), 0);
  return Math.min(8, Math.sqrt(total));
}

function eventFeatures(events: GPEvent[]) {
  return {
    type: "FeatureCollection" as const,
    features: events.flatMap((ev) => {
      const exact = ev.location ? [ev.location.lon, ev.location.lat] : null;
      const centroid = centroidFor(ev.country);
      if (!exact && !centroid) return [];
      let coords: [number, number];
      if (exact) coords = exact as [number, number];
      else {
        const [dx, dy] = jitter(ev.event_id);
        coords = [centroid![0] + dx, centroid![1] + dy];
      }
      return [{
        type: "Feature" as const,
        geometry: { type: "Point" as const, coordinates: coords },
        properties: {
          title: ev.title || `${ev.event_type} · ${ev.country}`,
          status: ev.verification_status,
          color: STATUS_COLOR[ev.verification_status] ?? "#41484C",
          radius: 5 + ev.confidence * 7 + impactBump(ev),
          exact: Boolean(exact),
          country: COUNTRY_NAMES.of(ev.country) ?? ev.country,
          date: fmt(ev.date_time),
          confidence: ev.confidence,
        },
      }];
    }),
  };
}

function transferFeatures(transfers: Transfer[]) {
  // aggregate supplier->recipient pairs
  const pairs = new Map<string, { from: [number, number]; to: [number, number]; n: number; supplier: string; recipient: string }>();
  for (const t of transfers) {
    const from = centroidFor(t.supplier);
    const to = centroidFor(t.recipient);
    if (!from || !to) continue;
    const key = `${t.supplier}→${t.recipient}`;
    const cur = pairs.get(key);
    if (cur) cur.n += 1;
    else pairs.set(key, { from, to, n: 1, supplier: t.supplier, recipient: t.recipient });
  }
  return {
    type: "FeatureCollection" as const,
    features: [...pairs.values()].map((p) => ({
      type: "Feature" as const,
      geometry: { type: "LineString" as const, coordinates: [p.from, p.to] },
      properties: {
        width: Math.min(5, 1 + Math.log2(p.n + 1)),
        label: `${p.supplier} → ${p.recipient}: ${p.n} documented transfer(s) — SIPRI Arms Transfers Database`,
      },
    })),
  };
}

export default function Home() {
  const mapDiv = useRef<HTMLDivElement>(null);
  const [events, setEvents] = useState<GPEvent[]>([]);
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [solutions, setSolutions] = useState<{
    country: string; created_at: string; engine: string;
    approaches: { level: string; title: string; approach: string; rationale: string;
                  enabling_actors: string[]; risks: string; what_would_make_this_wrong: string;
                  confidence: string }[];
  }[]>([]);
  const [hra, setHra] = useState<{
    statement: string; created_at: string; engine: string;
    vitals: Record<string, { pressure: number; vitals: Record<string, { score: number; level: string }> }>;
    priorities: { country: string; vital: string; level: string; dispatch: string; score: number; action: string }[];
    platform_audit: { overall?: string; recommendations?: string[]; exposure_risks?: string[] } | null;
  } | null>(null);
  const [err, setErr] = useState("");
  // contribution form
  const [cText, setCText] = useState("");
  const [cUrl, setCUrl] = useState("");
  const [cMsg, setCMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [cBusy, setCBusy] = useState(false);

  useEffect(() => {
    fetchJSON<GPEvent[]>("/api/public/events?limit=1000")
      .then(setEvents).catch((e) => setErr(String(e)));
    fetchJSON<{ transfers: Transfer[] }>("/api/public/arms-transfers?limit=1000")
      .then((d) => setTransfers(d.transfers)).catch(() => setTransfers([]));
    fetchJSON<typeof hra>("/api/public/hra/position")
      .then(setHra).catch(() => setHra(null));
    fetchJSON<typeof solutions>("/api/public/solutions")
      .then(setSolutions).catch(() => setSolutions([]));
  }, []);

  useEffect(() => {
    if (!mapDiv.current || events.length === 0) return;
    const map = new maplibregl.Map({
      container: mapDiv.current,
      style: {
        version: 8,
        glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
        sources: {
          countries: { type: "vector", url: "https://demotiles.maplibre.org/tiles/tiles.json" },
        },
        layers: [
          { id: "bg", type: "background", paint: { "background-color": "#dfe9e5" } },
          { id: "land", type: "fill", source: "countries", "source-layer": "countries",
            paint: { "fill-color": "#f7faf9", "fill-outline-color": "#b8c4bf" } },
          { id: "borders", type: "line", source: "countries", "source-layer": "countries",
            paint: { "line-color": "#a7b3ae", "line-width": 0.6 } },
        ],
      },
      center: [15, 12],
      zoom: 2.2,
      attributionControl: { compact: true },
    });
    map.on("error", (e) => {
      console.error("maplibre:", e.error);
      setErr((prev) => prev || `map: ${e.error?.message ?? "load failed"}`);
    });
    map.on("load", () => {
      // influence lines (documented arms transfers) under the event circles
      map.addSource("transfers", { type: "geojson", data: transferFeatures(transfers) });
      map.addLayer({
        id: "transfer-lines", type: "line", source: "transfers",
        paint: {
          "line-color": "#41484C", "line-opacity": 0.55,
          "line-width": ["get", "width"], "line-dasharray": [2, 1.5],
        },
      });
      // reviewed events — color encodes verification status, size encodes
      // confidence + reported civilian impact
      map.addSource("events", { type: "geojson", data: eventFeatures(events) });
      map.addLayer({
        id: "event-circles", type: "circle", source: "events",
        paint: {
          "circle-radius": ["get", "radius"],
          "circle-color": ["get", "color"],
          "circle-opacity": 0.75,
          "circle-stroke-color": "#2A353D",
          "circle-stroke-width": ["case", ["get", "exact"], 1.8, 0.8],
        },
      });
      map.on("click", "event-circles", (e: maplibregl.MapLayerMouseEvent) => {
        const p = e.features?.[0]?.properties;
        if (!p) return;
        new maplibregl.Popup().setLngLat(e.lngLat).setHTML(
          `<strong>${p.title}</strong><br/>${p.country} · ${p.date}<br/>` +
          `status: ${String(p.status).replace(/_/g, " ")} · confidence ${Number(p.confidence).toFixed(2)}<br/>` +
          `<em>${p.exact ? "exact location from source" : "country-level placement (jittered)"}</em>`,
        ).addTo(map);
      });
      map.on("click", "transfer-lines", (e: maplibregl.MapLayerMouseEvent) => {
        const p = e.features?.[0]?.properties;
        if (!p) return;
        new maplibregl.Popup().setLngLat(e.lngLat).setHTML(`<strong>${p.label}</strong>`).addTo(map);
      });
      for (const layer of ["event-circles", "transfer-lines"]) {
        map.on("mouseenter", layer, () => { map.getCanvas().style.cursor = "pointer"; });
        map.on("mouseleave", layer, () => { map.getCanvas().style.cursor = ""; });
      }
    });
    return () => map.remove();
  }, [events, transfers]);

  const submitContribution = async () => {
    setCBusy(true); setCMsg(null);
    try {
      const res = await fetch("/api/public/contributions", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text: cText.trim(), url: cUrl.trim() || null, website: "" }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(typeof body.detail === "string" ? body.detail : `HTTP ${res.status}`);
      }
      setCText(""); setCUrl("");
      setCMsg({ ok: true, text: "Received. Your contribution enters moderation as an unverified claim — it is never published automatically." });
    } catch (e) {
      setCMsg({ ok: false, text: e instanceof Error ? e.message : "Failed" });
    } finally {
      setCBusy(false);
    }
  };

  return (
    <div className="home">
      <div className="hero">
        <h2>Where reviewed events are happening</h2>
        <p>
          Circles are reviewed events — green shades passed human review;
          slate circles are AI-corroborated (institutional source, independent
          corroboration, no analyst-panel objections) and labeled as such until
          a human reviews them. Size reflects confidence and reported civilian
          impact. Dashed lines are documented
          arms transfers from the SIPRI Arms Transfers Database — relationships
          with sources, not accusations. Nothing here is a forecast, and
          nothing here is a ranking.
        </p>
      </div>
      {err && <div className="err">{err.startsWith("map:") ? `Map error — ${err.slice(4).trim()}` : `Could not load the public feed: ${err}`}</div>}
      <div className="home-cols">
        <div className="map-wrap">
          <div ref={mapDiv} className="map" aria-label="Map of reviewed events and documented transfers" />
          <div className="legend">
            <span><i className="sw" style={{ background: "#2B8C72" }} /> verified</span>
            <span><i className="sw" style={{ background: "#63CDA3" }} /> partially verified</span>
            <span><i className="sw" style={{ background: "#41484C" }} /> AI-corroborated (not human-verified)</span>
            <span><i className="sw line" /> documented arms transfers (SIPRI)</span>
            <span className="legend-note">circle size = confidence + civilian impact · thick outline = exact location</span>
          </div>
        </div>
        <div className="latest">
          <h3>Latest reviewed events</h3>
          {events.slice(0, 8).map((ev) => (
            <div className="pub-card" key={ev.event_id}>
              <div className="top">
                <span className="type-chip">{ev.event_type}</span>
                <span className={`badge b-${ev.verification_status}`}>
                  <span className="dot" />{ev.verification_status.replace("_", " ")}
                </span>
              </div>
              <span className="title">{ev.title || `${ev.event_type} · ${ev.country}`}</span>
              <span className="meta">
                {COUNTRY_NAMES.of(ev.country) ?? ev.country} · {fmt(ev.date_time)} · confidence {ev.confidence.toFixed(2)}
              </span>
              {ev.source_urls[0] && (
                <a className="srclink" href={ev.source_urls[0]} target="_blank" rel="noreferrer">source</a>
              )}
            </div>
          ))}
          {events.length === 0 && !err && <div className="empty">No reviewed events yet.</div>}

          <div className="contribute">
            <h3>Share information</h3>
            <p className="contribute-note">
              Seen something relevant? Submissions enter moderation as unverified
              claims and are checked against independent sources before any use.
              Please include no personal data.
            </p>
            <textarea
              placeholder="What happened, where, when — and how you know (min. 10 characters)"
              value={cText} onChange={(e) => setCText(e.target.value)} maxLength={2000}
            />
            <input
              placeholder="https://… supporting link (optional)"
              value={cUrl} onChange={(e) => setCUrl(e.target.value)}
            />
            {/* honeypot — hidden from humans, bots fill it */}
            <input className="hp" tabIndex={-1} autoComplete="off" aria-hidden="true" value="" readOnly />
            <button type="button" className="btn-primary" disabled={cBusy || cText.trim().length < 10} onClick={submitContribution}>
              Submit for review
            </button>
            {cMsg && <span className={cMsg.ok ? "ok" : "err"}>{cMsg.text}</span>}
          </div>
        </div>
      </div>
      {hra && (
        <div className="hra">
          <div className="hra-head">
            <h3>Human Rights Agent — published position</h3>
            <span className="hra-meta">{fmt(hra.created_at)} · {hra.engine} · independent algorithm; urgent items require human dispatch</span>
          </div>
          <p className="hra-statement">{hra.statement}</p>
          <div className="hra-cols">
            <div className="hra-vitals">
              {Object.entries(hra.vitals).sort((a, b) => b[1].pressure - a[1].pressure).map(([c, d]) => (
                <div className="hra-country" key={c}>
                  <span className="hra-cname">{COUNTRY_NAMES.of(c) ?? c}</span>
                  {Object.entries(d.vitals).filter(([, v]) => v.score > 0).map(([name, v]) => (
                    <div className="hra-vital" key={name} title={`${name}: ${v.score}`}>
                      <span className="hra-vlabel">{name.replace(/_/g, " ")}</span>
                      <span className="hra-bar"><i className={`lv-${v.level}`} style={{ width: `${Math.round(v.score * 100)}%` }} /></span>
                      <span className={`hra-lv lv-t-${v.level}`}>{v.level}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
            <div className="hra-actions">
              <h4>Prioritized diplomatic actions</h4>
              {hra.priorities.slice(0, 6).map((a, i) => (
                <div className="hra-action" key={i}>
                  <span className={`hra-lv lv-t-${a.level === "urgent" ? "alarm" : "concern"}`}>
                    {a.level}{a.dispatch === "human_required" ? " · human dispatch" : ""}
                  </span>
                  <span className="hra-atext"><strong>{COUNTRY_NAMES.of(a.country) ?? a.country}</strong> — {a.action}</span>
                </div>
              ))}
              {hra.platform_audit?.overall && (
                <div className="hra-selfaudit">
                  Self-audit of the platform: <strong>{hra.platform_audit.overall.replace(/_/g, " ")}</strong>
                  {(hra.platform_audit.recommendations ?? []).slice(0, 2).map((r) => <span key={r}> · {r}</span>)}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      {solutions.length > 0 && (
        <div className="hra solutions">
          <div className="hra-head">
            <h3>Suggested approaches for peace</h3>
            <span className="hra-meta">machine-drafted recommendations grounded in treated events — options for decision-makers, never commands; dispatch is human</span>
          </div>
          {solutions.map((s) => (
            <div className="sol-country" key={s.country}>
              <span className="hra-cname">{COUNTRY_NAMES.of(s.country) ?? s.country}</span>
              <div className="sol-grid">
                {s.approaches.map((a, i) => (
                  <details className="sol-card" key={i}>
                    <summary>
                      <span className={`sol-level l-${a.level}`}>{a.level}</span>
                      <span className="sol-title">{a.title}</span>
                      <span className="sol-conf">{a.confidence}</span>
                    </summary>
                    <p>{a.approach}</p>
                    <p className="sol-why"><strong>Why now:</strong> {a.rationale}</p>
                    <p className="sol-why"><strong>Enabling actors:</strong> {a.enabling_actors.join(", ")}</p>
                    <p className="sol-risk"><strong>Risks:</strong> {a.risks}</p>
                    <p className="sol-risk"><strong>What would make this wrong:</strong> {a.what_would_make_this_wrong}</p>
                  </details>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
