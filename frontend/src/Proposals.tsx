import { useEffect, useState } from "react";
import { COUNTRY_NAMES, fetchJSON, fmtDate } from "./mapdata";

/** Peace proposals — the solutions engine's published approaches, in their own
 * section, ordered by a TRANSPARENT priority score computed from the published
 * HRA position (treated events only):
 *
 *   priority = 0.35 × population impact (population_stability pressure)
 *            + 0.25 × health pressure   (health_system)
 *            + 0.25 × armed-violence pressure (civilian_safety)
 *            + 0.15 × poverty pressure  (poverty_and_livelihoods)
 *
 * Deliberately NOT a "war probability": the platform publishes no forecasts
 * (docs/GOVERNANCE.md). Every component is shown, every component is a 0..1
 * pressure score derived from cited, treated events with 14-day decay. */

const WEIGHTS = { population: 0.35, health: 0.25, violence: 0.25, poverty: 0.15 } as const;

interface SolutionSet {
  country: string; created_at: string; engine: string;
  approaches: { level: string; title: string; approach: string; rationale: string;
                enabling_actors: string[]; risks: string; what_would_make_this_wrong: string;
                confidence: string }[];
}

interface HraPosition {
  created_at: string; engine: string;
  vitals: Record<string, { pressure: number; vitals: Record<string, { score: number; level: string }> }>;
}

interface Ranked {
  set: SolutionSet;
  priority: number;
  components: { population: number; health: number; violence: number; poverty: number };
}

function rank(sets: SolutionSet[], hra: HraPosition | null): Ranked[] {
  const ranked = sets.map((set) => {
    const v = hra?.vitals[set.country]?.vitals ?? {};
    const components = {
      population: v.population_stability?.score ?? 0,
      health: v.health_system?.score ?? 0,
      violence: v.civilian_safety?.score ?? 0,
      poverty: v.poverty_and_livelihoods?.score ?? 0,
    };
    const priority =
      WEIGHTS.population * components.population +
      WEIGHTS.health * components.health +
      WEIGHTS.violence * components.violence +
      WEIGHTS.poverty * components.poverty;
    return { set, priority: Math.round(priority * 1000) / 1000, components };
  });
  return ranked.sort((a, b) => b.priority - a.priority);
}

function ComponentBar({ label, weight, value }: { label: string; weight: number; value: number }) {
  return (
    <div className="prio-component" title={`${label}: ${value.toFixed(3)} × weight ${weight}`}>
      <span className="prio-clabel">{label} <em>×{weight}</em></span>
      <span className="hra-bar"><i className="lv-concern" style={{ width: `${Math.round(value * 100)}%` }} /></span>
      <span className="prio-cval">{value.toFixed(2)}</span>
    </div>
  );
}

export default function Proposals() {
  const [sets, setSets] = useState<SolutionSet[]>([]);
  const [hra, setHra] = useState<HraPosition | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    fetchJSON<SolutionSet[]>("/api/public/solutions").then(setSets).catch((e) => setErr(String(e)));
    fetchJSON<HraPosition>("/api/public/hra/position").then(setHra).catch(() => setHra(null));
  }, []);

  const ranked = rank(sets, hra);

  return (
    <div className="home proposals-page">
      <div className="hero">
        <h2>Peace proposals</h2>
        <p>
          Machine-drafted approaches for decision-makers, grounded in treated
          events — options, never commands; dispatch is always human. Ordered
          by a transparent priority score, highest first.
        </p>
      </div>
      <div className="prio-method">
        <strong>How this list is ordered.</strong> priority =
        {" "}{WEIGHTS.population} × population impact (displacement pressure)
        {" "}+ {WEIGHTS.health} × health pressure
        {" "}+ {WEIGHTS.violence} × armed-violence pressure
        {" "}+ {WEIGHTS.poverty} × poverty pressure.
        Each component is a 0–1 pressure score from the published Human Rights
        Agent position: cited, treated events only, 14-day decay, per-country
        absolute conditions. This is situation pressure, <em>not a forecast of
        war</em> and not a ranking of countries — the platform publishes no
        probabilities of conflict. Weights follow the published prioritization
        policy (civilian impact first — DPG do-no-harm standard; prevention
        first — UN New Agenda for Peace; see docs/PRIORITIZATION.md).
        {hra && <span className="hra-meta"> Position of {fmtDate(hra.created_at)} · {hra.engine}.</span>}
      </div>
      {err && <div className="err">Could not load proposals: {err}</div>}
      {ranked.map(({ set, priority, components }, idx) => (
        <div className="hra solutions prio-block" key={set.country}>
          <div className="hra-head">
            <h3>
              <span className="prio-rank">#{idx + 1}</span>{" "}
              <a className="country-link" href={`#/country/${set.country}`}>
                {COUNTRY_NAMES.of(set.country) ?? set.country}
              </a>
              <span className="prio-score" title="composite priority, components below">
                priority {priority.toFixed(2)}
              </span>
            </h3>
            <span className="hra-meta">drafted {fmtDate(set.created_at)} · {set.engine}</span>
          </div>
          <div className="prio-components">
            <ComponentBar label="population impact" weight={WEIGHTS.population} value={components.population} />
            <ComponentBar label="health pressure" weight={WEIGHTS.health} value={components.health} />
            <ComponentBar label="armed-violence pressure" weight={WEIGHTS.violence} value={components.violence} />
            <ComponentBar label="poverty pressure" weight={WEIGHTS.poverty} value={components.poverty} />
          </div>
          <div className="sol-grid">
            {set.approaches.map((a, i) => (
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
      {ranked.length === 0 && !err && (
        <div className="empty">No published proposals yet — they appear once situations form from treated events.</div>
      )}
    </div>
  );
}
