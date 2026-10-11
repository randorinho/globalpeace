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
          Circles are events that passed human review — color shows how each
          report was treated (verified or partially verified), size reflects
          confidence and reported civilian impact. Dashed lines are documented
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
    </div>
  );
}
