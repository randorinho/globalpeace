// Shared map data helpers — used by the home map and the country pages.
import { centroidFor } from "./centroids";
import type { GPEvent } from "./types";

export const COUNTRY_NAMES = new Intl.DisplayNames(["en"], { type: "region" });

// Treatment colors — same tokens as the review dashboard badges.
export const STATUS_COLOR: Record<string, string> = {
  verified: "#2B8C72",
  partially_verified: "#63CDA3",
  ai_corroborated: "#37675D", // machine sea-green: trust family, muted — never impersonates human green
};

export const fmtDate = (iso: string) => iso.slice(0, 10);

/** Deterministic jitter so same-country events spread around the centroid
 *  without implying precision we don't have. */
export function jitter(id: string): [number, number] {
  let h = 0;
  for (const c of id) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  const angle = (h % 360) * (Math.PI / 180);
  const dist = 0.4 + ((h >>> 8) % 100) / 100;
  return [Math.cos(angle) * dist, Math.sin(angle) * dist * 0.7];
}

export function impactBump(ev: GPEvent): number {
  const total = Object.values(ev.civilian_impact ?? {}).reduce<number>(
    (acc, v) => acc + (typeof v === "number" ? v : 0), 0);
  return Math.min(8, Math.sqrt(total));
}

export function eventFeatures(events: GPEvent[]) {
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
          iso2: ev.country,
          country: COUNTRY_NAMES.of(ev.country) ?? ev.country,
          date: fmtDate(ev.date_time),
          confidence: ev.confidence,
        },
      }];
    }),
  };
}

/** Base style shared by the home map and country mini-maps. */
export function baseMapStyle() {
  return {
    version: 8 as const,
    glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
    sources: {
      countries: { type: "vector" as const, url: "https://demotiles.maplibre.org/tiles/tiles.json" },
    },
    layers: [
      { id: "bg", type: "background" as const, paint: { "background-color": "#dfe9e5" } },
      { id: "land", type: "fill" as const, source: "countries", "source-layer": "countries",
        paint: { "fill-color": "#f7faf9", "fill-outline-color": "#b8c4bf" } },
      { id: "borders", type: "line" as const, source: "countries", "source-layer": "countries",
        paint: { "line-color": "#a7b3ae", "line-width": 0.6 } },
    ],
  };
}

export async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
