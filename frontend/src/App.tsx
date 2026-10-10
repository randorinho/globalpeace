import { useCallback, useEffect, useMemo, useState } from "react";
import Home from "./Home";
import { fetchHistory, fetchQueue, postReview } from "./api";
import type { EventType, GPEvent, ReviewRecord, VerificationStatus } from "./types";

const STATUSES: VerificationStatus[] = ["verified", "partially_verified", "disputed", "retracted"];
const TYPES: EventType[] = ["protest", "attack", "negotiation", "displacement"];

const fmt = (iso: string) => iso.slice(0, 16).replace("T", " ") + " UTC";
const domain = (url: string) => { try { return new URL(url).hostname; } catch { return url; } };

function Badge({ status }: { status: VerificationStatus }) {
  return (
    <span className={`badge b-${status}`}>
      <span className="dot" />
      {status.replace("_", " ")}
    </span>
  );
}

function Card({ ev, selected, onClick }: { ev: GPEvent; selected: boolean; onClick: () => void }) {
  return (
    <button type="button" className={`card${selected ? " selected" : ""}`} onClick={onClick}>
      <div className="top">
        <span className="type-chip">{ev.event_type}</span>
        <span className="headline">{ev.country}</span>
        <Badge status={ev.verification_status} />
      </div>
      {ev.title && <span className="title">{ev.title}</span>}
      <span className="meta">
        {fmt(ev.date_time)} · conf {ev.confidence.toFixed(2)} · {ev.information_type}
      </span>
      {ev.source_urls[0] && <span className="src">{ev.source_urls[0]}</span>}
    </button>
  );
}

function Detail({ ev, reviewer, onReviewed }: { ev: GPEvent; reviewer: string; onReviewed: () => void }) {
  const [history, setHistory] = useState<ReviewRecord[]>([]);
  const [status, setStatus] = useState<VerificationStatus | null>(null);
  const [note, setNote] = useState("");
  const [consulted, setConsulted] = useState("");
  const [cCountry, setCCountry] = useState("");
  const [cType, setCType] = useState("");
  const [cConf, setCConf] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  useEffect(() => {
    setStatus(null); setNote(""); setConsulted(""); setCCountry(""); setCType(""); setCConf(""); setMsg(null);
    fetchHistory(ev.event_id).then(setHistory).catch(() => setHistory([]));
  }, [ev.event_id]);

  const canSubmit = !!status && note.trim().length >= 5 && !!reviewer && !busy;

  const submit = async () => {
    if (!status) return;
    setBusy(true); setMsg(null);
    const corrections: Record<string, unknown> = {};
    if (cCountry.trim()) corrections.country = cCountry.trim().toUpperCase();
    if (cType) corrections.event_type = cType;
    if (cConf !== "") corrections.confidence = Number(cConf);
    try {
      await postReview(ev.event_id, reviewer, {
        status,
        note: note.trim(),
        sources_consulted: consulted.split("\n").map((s) => s.trim()).filter(Boolean),
        ...(Object.keys(corrections).length ? { corrections } : {}),
      });
      setMsg({ ok: true, text: `Recorded: ${status.replace("_", " ")}` });
      onReviewed();
    } catch (e) {
      setMsg({ ok: false, text: e instanceof Error ? e.message : "Request failed" });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <h2>
        {ev.title || `${ev.event_type} · ${ev.country}`} <Badge status={ev.verification_status} />
      </h2>
      <p className="sub">Reported {fmt(ev.date_time)} · {ev.information_type} · {ev.source_language}</p>

      <dl className="kv">
        <dt>Event ID</dt><dd>{ev.event_id}</dd>
        <dt>Location</dt><dd>{ev.location ? `${ev.location.lat.toFixed(4)}, ${ev.location.lon.toFixed(4)}` : "—"}</dd>
        <dt>Actors</dt><dd>{ev.actors.length ? ev.actors.join(", ") : "—"}</dd>
        <dt>Sources</dt>
        <dd>
          {ev.source_urls.length
            ? ev.source_urls.map((u) => (
                <div key={u}><a href={u} target="_blank" rel="noreferrer">{domain(u)}</a> — {u}</div>
              ))
            : "—"}
        </dd>
        <dt>Confidence</dt>
        <dd>
          {ev.confidence.toFixed(2)}
          <div className="confbar"><div style={{ width: `${ev.confidence * 100}%` }} /></div>
        </dd>
      </dl>

      <div className="decision">
        <h3>Decision</h3>
        <div className="status-row">
          {STATUSES.map((s) => (
            <button key={s} type="button" className={`status-pill${status === s ? " on" : ""}`} onClick={() => setStatus(s)}>
              {s.replace("_", " ")}
            </button>
          ))}
        </div>
        <label>
          Why — required, this is the audit trail
          <textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="What did you check, and what did you conclude?" />
        </label>
        <label>
          Sources consulted (one URL per line)
          <textarea value={consulted} onChange={(e) => setConsulted(e.target.value)} placeholder="https://…" />
        </label>
        <div>
          <h3>Corrections (optional)</h3>
          <div className="corrections">
            <label>Country (ISO2)<input value={cCountry} onChange={(e) => setCCountry(e.target.value)} maxLength={2} placeholder={ev.country} /></label>
            <label>Event type
              <select value={cType} onChange={(e) => setCType(e.target.value)}>
                <option value="">unchanged</option>
                {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </label>
            <label>Confidence<input type="number" min="0" max="1" step="0.05" value={cConf} onChange={(e) => setCConf(e.target.value)} placeholder={String(ev.confidence)} /></label>
          </div>
        </div>
        <div className="submit-row">
          <button type="button" className="btn-primary" disabled={!canSubmit} onClick={submit}>
            Record decision
          </button>
          {!reviewer && <span className="err">Set your reviewer email in the top bar first.</span>}
          {msg && <span className={msg.ok ? "ok" : "err"}>{msg.text}</span>}
        </div>
      </div>

      {history.length > 0 && (
        <div className="history">
          <h3>History</h3>
          {history.map((h) => (
            <div className="hrow" key={h.review_id}>
              <div className="who">{fmt(h.created_at)} · {h.reviewer}</div>
              <div className="what">
                {h.previous_status.replace("_", " ")} → <strong>{h.new_status.replace("_", " ")}</strong>
                {Object.keys(h.changes).length > 0 && (
                  <> · {Object.entries(h.changes).map(([k, v]) => `${k}: ${String(v.from)} → ${String(v.to)}`).join(", ")}</>
                )}
              </div>
              <div className="note">{h.note}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ReviewPage() {
  const [queue, setQueue] = useState<GPEvent[]>([]);
  const [pending, setPending] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [country, setCountry] = useState("");
  const [etype, setEtype] = useState("");
  const [reviewer, setReviewer] = useState(() => localStorage.getItem("gp-reviewer") ?? "");
  const [loadErr, setLoadErr] = useState("");

  const load = useCallback(() => {
    fetchQueue({ country: country || undefined, event_type: etype || undefined })
      .then((d) => { setQueue(d.events); setPending(d.pending); setLoadErr(""); })
      .catch((e) => setLoadErr(e instanceof Error ? e.message : "Failed to load queue"));
  }, [country, etype]);

  useEffect(load, [load]);

  const countries = useMemo(() => [...new Set(queue.map((e) => e.country))].sort(), [queue]);
  const selected = queue.find((e) => e.event_id === selectedId) ?? null;

  return (
    <>
      <div className="topbar subbar">
        <span className="pending-chip">{pending} pending</span>
        <div className="spacer" />
        <input
          className="reviewer-input"
          placeholder="reviewer email (dev: X-Reviewer)"
          value={reviewer}
          onChange={(e) => { setReviewer(e.target.value); localStorage.setItem("gp-reviewer", e.target.value); }}
        />
      </div>
      <div className="cols">
        <div className="queue">
          <div className="filters">
            <select value={country} onChange={(e) => setCountry(e.target.value)} aria-label="Filter by country">
              <option value="">All countries</option>
              {countries.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            <select value={etype} onChange={(e) => setEtype(e.target.value)} aria-label="Filter by event type">
              <option value="">All types</option>
              {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          {loadErr && <div className="err">{loadErr}</div>}
          {queue.map((ev) => (
            <Card key={ev.event_id} ev={ev} selected={ev.event_id === selectedId} onClick={() => setSelectedId(ev.event_id)} />
          ))}
          {queue.length === 0 && !loadErr && <div className="empty">Queue is empty — nothing awaiting review.</div>}
        </div>
        <div className="detail">
          {selected
            ? <Detail ev={selected} reviewer={reviewer.trim()} onReviewed={load} />
            : <div className="empty">Select a claim from the queue to review it.</div>}
        </div>
      </div>
    </>
  );
}

export default function App() {
  const [route, setRoute] = useState(window.location.hash);
  const [theme, setTheme] = useState(() =>
    window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light",
  );

  useEffect(() => {
    const onHash = () => setRoute(window.location.hash);
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  const review = route === "#/review";

  return (
    <div className="app">
      <div className="topbar">
        <h1><span className="brand">globalpeace.ai</span></h1>
        <nav className="nav">
          <a href="#/" className={review ? "" : "on"}>Map</a>
          <a href="#/review" className={review ? "on" : ""}>Review</a>
        </nav>
        <div className="spacer" />
        <button type="button" className="theme-btn" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
          {theme === "dark" ? "Light" : "Dark"}
        </button>
      </div>
      {review ? <ReviewPage /> : <Home />}
    </div>
  );
}
