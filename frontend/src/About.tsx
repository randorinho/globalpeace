/** About page — what this platform is (and is not), how a claim becomes
 * publishable, and the rules that bind the machines. Content mirrors the
 * founding documents (README, docs/GOVERNANCE.md, docs/PRIORITIZATION.md). */

const JOURNEY: { step: string; detail: string }[] = [
  { step: "Ingest", detail: "Institutional sources (UN News, ReliefWeb, IOM, SIPRI) are fetched on a 30-minute cycle. Every item lands as an unverified claim — transparent keyword rules assign its type; items naming no country or matching no type are skipped and logged, never guessed." },
  { step: "Audit", detail: "A transparent rules engine scores each claim (source tier, recency, corroboration, specificity), then six continental analyst desks — each a panel of six AI agents with distinct lenses — add doubt: concrete, checkable concerns. Panels never verify." },
  { step: "Corroborate", detail: "A claim is promoted to ai-corroborated only when fail-closed criteria pass: institutional source, independent corroboration, fresh reporting, no panel objection shared by two or more analysts — and never when it names individuals or exact locations." },
  { step: "Human decision", detail: "Only a named human reviewer can mark anything verified, disputed or retracted. Every decision enters an append-only audit trail; machine opinions remain advisory, forever." },
  { step: "Publish", detail: "The public feed shows only verified, partially-verified, or explicitly machine-labeled events — each with a public verification trail anyone can inspect." },
];

const AGENTS: { role: string; count: string; body: string }[] = [
  { role: "Transparent rules engine", count: "deterministic — not an AI",
    body: "Scores every incoming claim against published criteria (source tier, recency, corroboration, specificity) and attaches its verdict, reasons and named cross-checks to the event. Its output is the shared starting point every other agent reads." },
  { role: "Continental analyst desks", count: "6 desks × 6 lenses = up to 36 AI analysts per cycle",
    body: "One desk per continent (Africa, Asia, Europe, North America, South America, Oceania). Each desk runs a panel of six independent AI analysts over the same regional digest, one lens each: source criticism, methodology, regional context, corroboration, temporal consistency, humanitarian impact. They interact only through aggregation: every concern is kept and attributed; a concern raised independently by two or more lenses becomes panel consensus. Panels output doubt only — any concern can downgrade a claim, none can upgrade or verify it." },
  { role: "Human Rights Agent", count: "1 agent, two mandates",
    body: "Mandate one — the immune system: a deterministic algorithm (no AI) scores six vital systems per country (civilian safety, population stability, food security, health system, humanitarian access, poverty & livelihoods) from treated events, weighted by verification status and decaying on a 14-day half-life, then prioritizes playbook actions — urgent ones always require human dispatch. Mandate two — an independent AI auditor of the platform itself: exposure risk, bias between countries, governance drift, manipulation surface. It drafts the public position statement from computed data only." },
  { role: "Solutions agents", count: "2 AI agents per tracked situation",
    body: "A political agent (dialogue formats, mediation tracks, regional-organisation engagement, confidence-building) and an economic agent (humanitarian financing, market stabilisation, trade and livelihood protection) each draft 2–3 concrete approaches per situation — grounded only in the cited events and vitals of that situation's digest, naming institutions only, each carrying rationale, risks, an explicit what-would-make-this-wrong, and a confidence grade." },
];

const RULES: { title: string; body: string }[] = [
  { title: "Machines propose, humans dispose", body: "No AI output verifies, dispatches, or escalates anything. Every consequential action requires a named, accountable human (APDSI letter, Art. 86-C spirit)." },
  { title: "The harm gate outranks accuracy", body: "If information could endanger a person, the platform must not publish it automatically — even when the information is accurate. Events naming individuals or exact locations always require human review." },
  { title: "No forecasts, no rankings", body: "The platform publishes situation pressure on vital systems — never probabilities of war, never league tables of countries, never merit or blame." },
  { title: "Same methodology for every country", body: "One registry, one audit standard, one published prioritization formula — applied identically from Sudan to Switzerland." },
  { title: "Everything auditable", body: "Open source (AGPL-3.0), open JSON APIs, public verification trails, append-only decision logs, and a published funding policy with a public ledger." },
];

export default function About() {
  return (
    <div className="home about-page">
      <div className="hero">
        <h2>About globalpeace.ai</h2>
        <p>
          An open, global peace-intelligence platform: it turns verified
          information into understanding, early warning, and concrete options
          for peace — while keeping every critical decision under human
          responsibility.
        </p>
      </div>

      <div className="prio-method">
        <strong>What this is not.</strong> This is not an autonomous agent
        making diplomatic decisions, and it does not promise to end wars. The
        system collects signals, verifies claims, explains risks, and
        recommends options to diplomats and authorised organisations. It
        supports existing UN structures for prevention, mediation and
        peacebuilding — it does not replace them. Final decisions remain
        human, institutional, and legally accountable.
      </div>

      <div className="hra">
        <div className="hra-head">
          <h3>How a claim becomes publishable</h3>
          <span className="hra-meta">every published event carries this journey as a public verification trail</span>
        </div>
        <div className="journey about-journey">
          {JOURNEY.map((j) => (
            <div className="step s-done" key={j.step}>
              <span className="step-dot" />
              <span className="step-label">{j.step}</span>
              <span className="step-detail">{j.detail}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="hra">
        <div className="hra-head">
          <h3>The agent system, functionally</h3>
          <span className="hra-meta">one pipeline cycle every 30 minutes; all machine output advisory, budget-capped, with a kill switch</span>
        </div>
        <p className="funding-none">
          Each cycle runs a fixed sequence: ingest → rules audit → analyst
          panels → fail-closed promotion → Human Rights Agent → solutions →
          publish. Agents never talk to each other directly — each stage reads
          the recorded output of the previous one, so every influence on a
          published event is inspectable in its verification trail.
        </p>
        <div className="sol-grid">
          {AGENTS.map((a) => (
            <div className="sol-card funding-card" key={a.role}>
              <span className="sol-title">{a.role}</span>
              <span className="hra-meta">{a.count}</span>
              <p>{a.body}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="hra">
        <div className="hra-head"><h3>The data it works from</h3></div>
        <p className="funding-none">
          Institutional feeds fetched every cycle: UN News, ReliefWeb (including
          IOM displacement reporting), the UCDP georeferenced event dataset, and
          SIPRI arms-transfer records; geolocation against the GeoNames
          gazetteer; plus moderated public contributions from the map page.
          Everything enters as an unverified claim — no source, machine or
          human, is trusted by default. Panels may name primary datasets
          (UNHCR, ACLED, FEWS NET, WHO) a human must check, but only a named
          reviewer records verification.
        </p>
      </div>

      <div className="hra">
        <div className="hra-head"><h3>From analysis to peace proposals</h3></div>
        <p className="funding-none">
          The solutions agents' approaches are published on the{" "}
          <a href="#/proposals">proposals page</a>, ordered by a fully
          transparent priority score computed from the Human Rights Agent's
          published vitals: 0.35 × population-stability pressure + 0.25 ×
          health-system pressure + 0.25 × civilian-safety pressure + 0.15 ×
          poverty pressure — every component a 0–1 score derived from cited,
          treated events. Deliberately not a war probability: the platform
          publishes pressures and options, never forecasts. Proposals are
          options for diplomats and authorised organisations — machine-drafted,
          human-dispatched, never commands.
        </p>
      </div>

      <div className="hra">
        <div className="hra-head"><h3>The rules that bind the machines</h3></div>
        <div className="sol-grid">
          {RULES.map((r) => (
            <div className="sol-card funding-card" key={r.title}>
              <span className="sol-title">{r.title}</span>
              <p>{r.body}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="hra">
        <div className="hra-head"><h3>Anchored in public frameworks</h3></div>
        <p className="funding-none">
          What the platform emphasizes, orders, or recommends traces to
          published frameworks, never to model preference: the UN's{" "}
          <em>Pact for the Future</em> and <em>Global Digital Compact</em>{" "}
          (information integrity), the Secretary-General's{" "}
          <em>New Agenda for Peace</em> (prevention first), and the{" "}
          <em>DPG Standard</em>'s do-no-harm principle (civilian impact
          first). The full policy, with every ordering surface mapped to its
          anchor, is public:{" "}
          <a href="https://github.com/randorinho/globalpeace/blob/main/docs/PRIORITIZATION.md" target="_blank" rel="noreferrer">
            docs/PRIORITIZATION.md
          </a>.
        </p>
      </div>

      <div className="hra">
        <div className="hra-head"><h3>Open by constitution</h3></div>
        <p className="funding-none">
          The platform is free software (AGPL-3.0) with a public repository,
          open JSON APIs, and a Digital Public Good application under review
          (submitted November 2026). It is an independent, Portuguese-led open
          project — ownership and maintainer are documented in the{" "}
          <a href="https://github.com/randorinho/globalpeace/blob/main/README.md#ownership-and-license" target="_blank" rel="noreferrer">
            repository's ownership statement
          </a>, with a published <a href="#/funding">funding policy</a>, a{" "}
          <a href="#/privacy">privacy-by-minimisation posture</a>, and a{" "}
          <a href="https://github.com/randorinho/globalpeace/blob/main/CODE_OF_CONDUCT.md" target="_blank" rel="noreferrer">code of conduct</a>.
          Source, documentation and verification methodology:{" "}
          <a href="https://github.com/randorinho/globalpeace" target="_blank" rel="noreferrer">github.com/randorinho/globalpeace</a>.
          Seen something relevant where you are? Use the contribution form on
          the <a href="#/">map page</a> — submissions enter moderation as
          unverified claims and are checked before any use.
        </p>
      </div>
    </div>
  );
}
