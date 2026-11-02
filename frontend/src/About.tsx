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
          (submitted November 2026). It is built and maintained by{" "}
          <strong>Ricardo Andorinho</strong> (Portugal), with a published{" "}
          <a href="#/funding">funding policy</a>, a{" "}
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
