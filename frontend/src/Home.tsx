import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef, useState } from "react";
import type { GPEvent } from "./types";

// Country centroids for the pilot set — events are aggregated per country so
// the map never implies more location precision than reviewers confirmed.
const CENTROIDS: Record<string, [number, number]> = {
  SD: [30.2, 15.6],
  TD: [18.7, 15.4],
  SS: [30.3, 7.3],
  CD: [23.7, -2.9],
  HT: [-72.7, 18.9],
};
const COUNTRY_NAMES = new Intl.DisplayNames(["en"], { type: "region" });

const fmt = (iso: string) => iso.slice(0, 10);

async function fetchPublicEvents(): Promise<GPEvent[]> {
  const res = await fetch("/api/public/events?limit=1000");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function buildCountryGeoJSON(events: GPEvent[]) {
  const byCountry = new Map<string, GPEvent[]>();
  for (const ev of events) {
    if (!byCountry.has(ev.country)) byCountry.set(ev.country, []);
    byCountry.get(ev.country)!.push(ev);
  }
  return {
    type: "FeatureCollection" as const,
    features: [...byCountry.entries()]
      .filter(([c]) => CENTROIDS[c])
      .map(([c, evs]) => {
        const types = evs.reduce<Record<string, number>>((acc, e) => {
          acc[e.event_type] = (acc[e.event_type] ?? 0) + 1;
          return acc;
        }, {});
        return {
          type: "Feature" as const,
          geometry: { type: "Point" as const, coordinates: CENTROIDS[c] },
          properties: {
            country: c,
            name: COUNTRY_NAMES.of(c) ?? c,
            count: evs.length,
            summary: Object.entries(types).map(([t, n]) => `${n} ${t}`).join(" · "),
          },
        };
      }),
  };
}

function buildDotGeoJSON(events: GPEvent[]) {
  return {
    type: "FeatureCollection" as const,
    features: events
      .filter((e) => e.location)
      .map((e) => ({
        type: "Feature" as const,
        geometry: { type: "Point" as const, coordinates: [e.location!.lon, e.location!.lat] },
        properties: { title: e.title || e.event_type, type: e.event_type },
      })),
  };
}

export default function Home() {
  const mapDiv = useRef<HTMLDivElement>(null);
  const [events, setEvents] = useState<GPEvent[]>([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    fetchPublicEvents().then(setEvents).catch((e) => setErr(String(e)));
  }, []);

  useEffect(() => {
    if (!mapDiv.current || events.length === 0) return;
    const map = new maplibregl.Map({
      container: mapDiv.current,
      // Inline style over the free demotiles vector source; production
      // self-hosts its own tiles. Inline = no dependency on the remote
      // style's layer stack or fonts.
      style: {
        version: 8,
        glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
        sources: {
          countries: {
            type: "vector",
            url: "https://demotiles.maplibre.org/tiles/tiles.json",
          },
        },
        layers: [
          { id: "bg", type: "background", paint: { "background-color": "#dfe9e5" } },
          {
            id: "land",
            type: "fill",
            source: "countries",
            "source-layer": "countries",
            paint: { "fill-color": "#f7faf9", "fill-outline-color": "#b8c4bf" },
          },
          {
            id: "borders",
            type: "line",
            source: "countries",
            "source-layer": "countries",
            paint: { "line-color": "#a7b3ae", "line-width": 0.6 },
          },
        ],
      },
      center: [15, 12],
      zoom: 2.2,
      attributionControl: { compact: true },
    });
    map.on("error", (e) => {
      // Surface silent tile/style failures instead of a blank map
      console.error("maplibre:", e.error);
      setErr((prev) => prev || `map: ${e.error?.message ?? "load failed"}`);
    });
    map.on("load", () => {
      map.addSource("countries", { type: "geojson", data: buildCountryGeoJSON(events) });
      map.addLayer({
        id: "country-circles",
        type: "circle",
        source: "countries",
        paint: {
          "circle-radius": ["+", 10, ["*", 6, ["sqrt", ["get", "count"]]]],
          "circle-color": "#2B8C72",
          "circle-opacity": 0.35,
          "circle-stroke-color": "#2B8C72",
          "circle-stroke-width": 2,
        },
      });
      map.addLayer({
        id: "country-labels",
        type: "symbol",
        source: "countries",
        layout: {
          "text-field": ["concat", ["get", "name"], "\n", ["get", "count"]],
          "text-size": 12,
          "text-font": ["Noto Sans Regular"],
        },
        paint: { "text-color": "#2A353D", "text-halo-color": "#ffffff", "text-halo-width": 1.5 },
      });
      map.addSource("dots", { type: "geojson", data: buildDotGeoJSON(events) });
      map.addLayer({
        id: "event-dots",
        type: "circle",
        source: "dots",
        paint: {
          "circle-radius": 5,
          "circle-color": "#FDAC11",
          "circle-stroke-color": "#2A353D",
          "circle-stroke-width": 1.5,
        },
      });
      map.on("click", "country-circles", (e: maplibregl.MapLayerMouseEvent) => {
        const p = e.features?.[0]?.properties;
        if (!p) return;
        new maplibregl.Popup()
          .setLngLat(e.lngLat)
          .setHTML(`<strong>${p.name}</strong><br/>${p.count} reviewed event(s)<br/>${p.summary}`)
          .addTo(map);
      });
      map.on("mouseenter", "country-circles", () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", "country-circles", () => { map.getCanvas().style.cursor = ""; });
    });
    return () => map.remove();
  }, [events]);

  return (
    <div className="home">
      <div className="hero">
        <h2>Where reviewed events are happening</h2>
        <p>
          Every point on this map passed human review. Circles aggregate events at
          country level; exact locations appear only where sources published them.
          Nothing here is a forecast, and nothing here is a ranking.
        </p>
      </div>
      {err && <div className="err">Could not load the public feed: {err}</div>}
      <div className="home-cols">
        <div ref={mapDiv} className="map" aria-label="Map of reviewed events" />
        <div className="latest">
          <h3>Latest reviewed events</h3>
          {events.slice(0, 12).map((ev) => (
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
                <a className="srclink" href={ev.source_urls[0]} target="_blank" rel="noreferrer">
                  source
                </a>
              )}
            </div>
          ))}
          {events.length === 0 && !err && <div className="empty">No reviewed events yet.</div>}
        </div>
      </div>
    </div>
  );
}
