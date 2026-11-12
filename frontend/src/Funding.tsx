/** Public funding page — principle #3 of the funding model (docs/FUNDING.md):
 * radical transparency. Every grant and donation will be published here
 * (amount, source, purpose). Until the first one exists, this page publishes
 * the rules money must follow to enter. */

const PRINCIPLES: { title: string; body: string }[] = [
  {
    title: "Independence",
    body: "No single funder above 30% of annual budget once past seed stage. " +
      "Funding never buys influence over verification, audit criteria, or the " +
      "Human Rights Agent's published positions.",
  },
  {
    title: "Exclusions",
    body: "No funding from parties to conflicts we track, from arms producers " +
      "or brokers, or from any source conditioning editorial outcomes.",
  },
  {
    title: "Radical transparency",
    body: "Every grant and donation is published on this page — amount, source, " +
      "purpose — with an annual external audit once funded.",
  },
  {
    title: "Public-good lock",
    body: "The platform remains open source (AGPL-3.0). Funding builds the " +
      "commons; it never finances a proprietary fork.",
  },
];

const PACKAGES: { name: string; what: string }[] = [
  { name: "Operational base", what: "Hosting, backups, monitoring, security audits — keeping the public feed dependable." },
  { name: "Verification depth", what: "ACLED / UNHCR / UCDP integrations, geolocation, multilingual coverage — the early-warning data commons." },
  { name: "Solutions engine", what: "Briefings, human-dispatch workflow, outcome tracking — measurable peace impact." },
  { name: "Governance", what: "Scientific and peace councils, external audits, published methodology — institutional strengthening." },
];

export default function Funding() {
  return (
    <div className="home funding-page">
      <div className="hero">
        <h2>Funding — public, non-profit, and published</h2>
        <p>
          This platform is an open public good. It accepts public and
          philanthropic funding under rules designed to keep it independent —
          and it publishes every contribution it receives, here.
        </p>
      </div>

      <div className="hra">
        <div className="hra-head">
          <h3>Current funding</h3>
          <span className="hra-meta">updated 2026-11-12</span>
        </div>
        <p className="funding-none">
          The platform has received <strong>no external funding to date</strong>.
          It is built and operated by its maintainer. Contributions can now be
          made through{" "}
          <a href="https://opencollective.com/globalpeaceai" target="_blank" rel="noreferrer">
            Open Collective
          </a>
          , where the collective is fiscally hosted by Open Source Europe and
          every transaction appears on a public ledger. Each grant or donation
          received is also published on this page with amount, source, and
          purpose. Registration as a Digital Public Good is in
          progress — see the repository's{" "}
          <a href="https://github.com/randorinho/globalpeace/blob/main/docs/FUNDING.md" target="_blank" rel="noreferrer">
            funding model
          </a>{" "}
          for the full plan.
        </p>
      </div>

      <div className="hra">
        <div className="hra-head"><h3>Principles — conditions for money to enter</h3></div>
        <div className="sol-grid">
          {PRINCIPLES.map((p) => (
            <div className="sol-card funding-card" key={p.title}>
              <span className="sol-title">{p.title}</span>
              <p>{p.body}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="hra">
        <div className="hra-head"><h3>What funding buys</h3></div>
        <div className="sol-grid">
          {PACKAGES.map((p) => (
            <div className="sol-card funding-card" key={p.name}>
              <span className="sol-title">{p.name}</span>
              <p>{p.what}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="prio-method">
        <strong>Why fund this.</strong> A live platform, an open public
        repository (AGPL-3.0, DCO-signed), transparent audit criteria, an
        independent Human Rights Agent that audits the platform itself, and
        append-only logs external authorities can inspect. The methodology is
        published for every country equally — that is what your funding keeps
        independent.
      </div>
    </div>
  );
}
