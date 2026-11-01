import * as maplibregl from "maplibre-gl";
import maplibreWorkerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef, useState } from "react";
import { centroidFor } from "./centroids";
import { COUNTRY_NAMES, STATUS_COLOR, baseMapStyle, eventFeatures, fetchJSON, fmtDate } from "./mapdata";
import type { GPEvent } from "./types";

maplibregl.setWorkerUrl(maplibreWorkerUrl);

const MONTHS = ["January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"];

interface Transfer {
  supplier: string; recipient: string; designation?: string;
  delivery_year?: string; source?: string; [k: string]: unknown;
}

interface Trail {
  event_id: string;
  status: string;
  ingested: { information_type: string; source_language: string };
  rules_audit: { verdict: string; score: number; cross_checks: Record<string, string> } | null;
  analyst_panel: { desk: string; panelists: number; concern_count: number; consensus_objections: number } | null;
  decisions: { at: string; to: string; actor: string }[];
}

interface HraPosition {
  statement: string; created_at: string; engine: string;
  vitals: Record<string, { pressure: number; vitals: Record<string, { score: number; level: string }> }>;
  priorities: { country: string; vital: string; level: string; dispatch: string; score: number; action: string }[];
}

interface SolutionSet {
  country: string; created_at: string; engine: string;
  approaches: { level: string; title: string; approach: string; rationale: string;
                enabling_actors: string[]; risks: string; what_would_make_this_wrong: string;
                confidence: string }[];
}

function pressureLabel(p: number): { label: string; cls: string } | null {
  if (p >= 0.66) return { label: "alarm", cls: "alarm" };
  if (p >= 0.45) return { label: "severe", cls: "severe" };
  if (p >= 0.33) return { label: "concern", cls: "concern" };
  if (p > 0.05) return { label: "watch", cls: "watch" };
  return null;
}

/** Lazy verification trail — fetched the first time the row is opened. */
function TrailBlock({ eventId }: { eventId: string }) {
  const [trail, setTrail] = useState<Trail | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    fetchJSON<Trail>(`/api/public/events/${eventId}/trail`)
      .then(setTrail).catch(() => setFailed(true));
  }, [eventId]);
  if (failed) return <span className="t-caption">Verification trail unavailable.</span>;
  if (!trail) return <span className="t-caption">Loading verification trail…</span>;
  return (
    <div className="tl-trail">
      <div className="journey">
        <div className="step s-done"><span className="step-dot" /><span className="step-label">Ingested</span>
          <span className="step-detail">{trail.ingested.information_type} · {trail.ingested.source_language}</span></div>
        <div className={`step ${trail.rules_audit ? "s-done" : "s-off"}`}><span className="step-dot" /><span className="step-label">Rules audit</span>
          <span className="step-detail">{trail.rules_audit ? `score ${Number(trail.rules_audit.score).toFixed(2)} · ${Object.keys(trail.rules_audit.cross_checks ?? {}).length} cross-check(s)` : "—"}</span></div>
        <div className={`step ${trail.analyst_panel ? (trail.analyst_panel.consensus_objections > 0 ? "s-warn" : "s-done") : "s-off"}`}><span className="step-dot" /><span className="step-label">Analyst panel</span>
          <span className="step-detail">{trail.analyst_panel ? `${trail.analyst_panel.panelists} agents · ${trail.analyst_panel.concern_count} concern(s)` : "—"}</span></div>
        <div className={`step ${trail.status === "ai_corroborated" || trail.decisions.length > 0 ? "s-done" : "s-off"}`}><span className="step-dot" /><span className="step-label">Decision</span>
          <span className="step-detail">{trail.decisions.length > 0 ? `${trail.decisions[trail.decisions.length - 1].to.replace(/_/g, " ")} — ${trail.decisions[trail.decisions.length - 1].actor}` : "—"}</span></div>
      </div>
      {trail.rules_audit && Object.keys(trail.rules_audit.cross_checks ?? {}).length > 0 && (
        <ul className="tl-checks">
          {Object.entries(trail.rules_audit.cross_checks).map(([k, v]) => (
            <li key={k}><strong>{k.replace(/_/g, " ")}</strong>: {v}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function Country({ iso2 }: { iso2: string }) {
  const mapDiv = useRef<HTMLDivElement>(null);
  const [events, setEvents] = useState<GPEvent[]>([]);
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [hra, setHra] = useState<HraPosition | null>(null);
  const [solutions, setSolutions] = useState<SolutionSet[]>([]);
  const [err, setErr] = useState("");
  const [opened, setOpened] = useState<Set<string>>(new Set());

  const name = COUNTRY_NAMES.of(iso2) ?? iso2;

  useEffect(() => {
    setEvents([]); setErr(""); setOpened(new Set());
    fetchJSON<GPEvent[]>("/api/public/events?limit=2000")
      .then((all) => setEvents(all.filter((e) => e.country === iso2)))
      .catch((e) => setErr(String(e)));
    fetchJSON<{ transfers: Transfer[] }>(`/api/public/arms-transfers?country=${iso2}&limit=200`)
      .then((d) => setTransfers(d.transfers)).catch(() => setTransfers([]));
    fetchJSON<HraPosition>("/api/public/hra/position").then(setHra).catch(() => setHra(null));
    fetchJSON<SolutionSet[]>("/api/public/solutions")
      .then((all) => setSolutions(all.filter((s) => s.country === iso2)))
      .catch(() => setSolutions([]));
  }, [iso2]);

  useEffect(() => {
    if (!mapDiv.current) return;
    const center = centroidFor(iso2) ?? [15, 12];
    const map = new maplibregl.Map({
      container: mapDiv.current,
      style: baseMapStyle() as maplibregl.StyleSpecification,
      center: center as [number, number],
      zoom: 4,
      attributionControl: { compact: true },
    });
    map.on("load", () => {
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
          `<strong>${p.title}</strong><br/>${p.date} · status: ${String(p.status).replace(/_/g, " ")}<br/>` +
          `<em>${p.exact ? "exact location from source" : "country-level placement (jittered)"}</em>`,
        ).addTo(map);
      });
      map.on("mouseenter", "event-circles", () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", "event-circles", () => { map.getCanvas().style.cursor = ""; });
    });
    return () => map.remove();
  }, [iso2, events]);

  // timeline: newest first, grouped by month
  const byMonth = new Map<string, GPEvent[]>();
  for (const ev of [...events].sort((a, b) => b.date_time.localeCompare(a.date_time))) {
    const key = ev.date_time.slice(0, 7);
    byMonth.set(key, [...(byMonth.get(key) ?? []), ev]);
  }
  const monthTitle = (key: string) => `${MONTHS[Number(key.slice(5, 7)) - 1]} ${key.slice(0, 4)}`;

  const countryVitals = hra?.vitals[iso2] ?? null;
  const pressure = countryVitals ? pressureLabel(countryVitals.pressure) : null;
  const priorities = (hra?.priorities ?? []).filter((p) => p.country === iso2);

  return (
    <div className="home country-page">
      <div className="hero cp-head">
        <a className="cp-back" href="#/">← World map</a>
        <h2>{name}</h2>
        <p className="cp-stats">
          {events.length} published event(s)
          {events.length > 0 && <> · latest {fmtDate(events.map((e) => e.date_time).sort().at(-1)!)}</>}
          {pressure && (
            <span className={`hra-lv lv-t-${pressure.cls}`} title={`HRA conflict pressure ${countryVitals!.pressure.toFixed(2)}`}>
              {" "}pressure: {pressure.label}
            </span>
          )}
        </p>
        <p>
          Everything on this page passed the platform's treatment ladder —
          sources cited, audits on record, machine labels explicit. Nothing
          here is a forecast, and nothing here is a ranking.
        </p>
      </div>
      {err && <div className="err">Could not load the public feed: {err}</div>}
      <div className="home-cols">
        <div className="map-wrap">
          <div ref={mapDiv} className="map" aria-label={`Map of reviewed events in ${name}`} />
          <div className="legend">
            <span><i className="sw" style={{ background: STATUS_COLOR.verified }} /> verified</span>
            <span><i className="sw" style={{ background: STATUS_COLOR.partially_verified }} /> partially verified</span>
            <span><i className="sw" style={{ background: STATUS_COLOR.ai_corroborated }} /> AI-corroborated</span>
          </div>
        </div>
        <div className="latest cp-timeline">
          <h3>Timeline</h3>
          {[...byMonth.entries()].map(([month, list]) => (
            <div className="tl-month" key={month}>
              <span className="tl-month-label">{monthTitle(month)}</span>
              {list.map((ev) => (
                <details
                  className="tl-item" key={ev.event_id}
                  onToggle={(e) => {
                    if ((e.target as HTMLDetailsElement).open)
                      setOpened((prev) => new Set(prev).add(ev.event_id));
                  }}
                >
                  <summary>
                    <span className="tl-date">{fmtDate(ev.date_time)}</span>
                    <span className="type-chip">{ev.event_type}</span>
                    <span className="tl-title">{ev.title || `${ev.event_type} · ${ev.country}`}</span>
                    <span className={`badge b-${ev.verification_status}`}>
                      <span className="dot" />{ev.verification_status.replace(/_/g, " ")}
                    </span>
                  </summary>
                  <div className="tl-body">
                    <span className="meta">confidence {ev.confidence.toFixed(2)} · {ev.information_type} · {ev.source_language}</span>
                    {ev.source_urls[0] && (
                      <a className="srclink" href={ev.source_urls[0]} target="_blank" rel="noreferrer">source</a>
                    )}
                    {opened.has(ev.event_id) && <TrailBlock eventId={ev.event_id} />}
                  </div>
                </details>
              ))}
            </div>
          ))}
          {events.length === 0 && !err && (
            <div className="empty">
              No published events for {name} yet. Events appear here once they
              pass audit and corroboration — claims under review never show.
            </div>
          )}
        </div>
      </div>

      {countryVitals && (
        <div className="hra">
          <div className="hra-head">
            <h3>Vital systems under pressure — {name}</h3>
            <span className="hra-meta">{hra && fmtDate(hra.created_at)} · {hra?.engine} · HRA vitals; urgent items require human dispatch</span>
          </div>
          <div className="hra-cols">
            <div className="hra-vitals">
              <div className="hra-country">
                {Object.entries(countryVitals.vitals).filter(([, v]) => v.score > 0).map(([vname, v]) => (
                  <div className="hra-vital" key={vname} title={`${vname}: ${v.score}`}>
                    <span className="hra-vlabel">{vname.replace(/_/g, " ")}</span>
                    <span className="hra-bar"><i className={`lv-${v.level}`} style={{ width: `${Math.round(v.score * 100)}%` }} /></span>
                    <span className={`hra-lv lv-t-${v.level}`}>{v.level}</span>
                  </div>
                ))}
              </div>
            </div>
            {priorities.length > 0 && (
              <div className="hra-actions">
                <h4>Prioritized diplomatic actions</h4>
                {priorities.slice(0, 6).map((a, i) => (
                  <div className="hra-action" key={i}>
                    <span className={`hra-lv lv-t-${a.level === "urgent" ? "alarm" : "concern"}`}>
                      {a.level}{a.dispatch === "human_required" ? " · human dispatch" : ""}
                    </span>
                    <span className="hra-atext">{a.action}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {solutions.map((s) => (
        <div className="hra solutions" key={s.country}>
          <div className="hra-head">
            <h3>Suggested approaches for peace — {name}</h3>
            <span className="hra-meta">machine-drafted options for decision-makers, never commands; dispatch is human</span>
          </div>
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

      {transfers.length > 0 && (
        <div className="hra">
          <div className="hra-head">
            <h3>Documented arms transfers — {name}</h3>
            <span className="hra-meta">SIPRI Arms Transfers Database · relationships with sources, not accusations</span>
          </div>
          <div className="cp-transfers">
            {transfers.slice(0, 12).map((t, i) => (
              <div className="hrow" key={i}>
                <div className="who">{t.delivery_year ?? "—"}</div>
                <div className="what"><strong>{t.supplier}</strong> → <strong>{t.recipient}</strong>{t.designation ? ` · ${t.designation}` : ""}</div>
              </div>
            ))}
            {transfers.length > 12 && <span className="t-caption">{transfers.length - 12} more on record.</span>}
          </div>
        </div>
      )}
    </div>
  );
}
