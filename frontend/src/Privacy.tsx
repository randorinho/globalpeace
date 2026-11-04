/** Privacy & legal page — the platform's data posture, stated publicly.
 * Truthful by construction: there are no accounts, no trackers, and the
 * contribution form actively rejects personal data. */

export default function Privacy() {
  return (
    <div className="home privacy-page">
      <div className="hero">
        <h2>Privacy &amp; legal</h2>
        <p>
          This platform is built on data minimisation: it works without
          knowing who you are. Jurisdiction: Portugal / European Union.
        </p>
      </div>

      <div className="hra">
        <div className="hra-head"><h3>Controller &amp; processors</h3></div>
        <ul className="legal-list">
          <li><strong>Data controller:</strong> MBU iNtelligence, Lda (NIPC 506988198),
              Av. Dr. Francisco Sá Carneiro 58, 1.º, 7000-757 Évora, Portugal —{" "}
              contact@globalpeace.ai.</li>
          <li><strong>Processors:</strong> Cloudflare, Inc. (edge hosting, CDN and security, USA);
              Anthropic, PBC (AI auditing of published institutional conflict reporting, USA);
              Hetzner Online GmbH (backend hosting, Germany, EU).</li>
          <li><strong>International transfers:</strong> Cloudflare and Anthropic process data in the
              United States under the EU-U.S. Data Privacy Framework and, where applicable,
              Standard Contractual Clauses.</li>
          <li>The map's fonts and country boundaries (MapLibre demo tiles) are served through this
              site's own edge proxy — your IP address is never sent to the tile provider.</li>
          <li>Public contributions are reviewed by humans only; their text is not sent to
              AI models.</li>
        </ul>
      </div>

      <div className="hra">
        <div className="hra-head"><h3>What we do not collect</h3></div>
        <ul className="legal-list">
          <li>No user accounts, no registration, no login for the public site.</li>
          <li>No tracking cookies, no analytics scripts, no advertising, no fingerprinting.</li>
          <li>Your theme preference and (for reviewers) a reviewer identifier are stored in your browser's
              localStorage only — they never leave your device.</li>
          <li>Rate-limiting on the public contribution endpoint uses a hashed, in-memory key derived from the
              connecting address; it is never written to disk and cannot be traced back to you.</li>
        </ul>
      </div>

      <div className="hra">
        <div className="hra-head"><h3>Public contributions</h3></div>
        <ul className="legal-list">
          <li>Submissions are screened and <strong>rejected if they contain personal data</strong> (email
              addresses, phone numbers) — testimonies are pseudonymised by design.</li>
          <li>Accepted submissions enter a human moderation queue as unverified claims; they are never
              published automatically.</li>
        </ul>
      </div>

      <div className="hra">
        <div className="hra-head"><h3>What we publish, and the harm gate</h3></div>
        <ul className="legal-list">
          <li>Published content is conflict-related reporting from attributed institutional sources —
              non-personal by design.</li>
          <li>Exposure gate: events naming individuals or exact coordinates are never published by machine
              decision — human review is required (docs/GOVERNANCE.md). The core safety rule: if information
              could endanger a person, the platform must not publish it automatically, even when accurate.</li>
          <li>Corrections: every published event carries a public verification trail, and a public
              correction mechanism exists. To request a correction or removal, write to
              contact@globalpeace.ai — requests are answered within 30 days.</li>
        </ul>
      </div>

      <div className="hra">
        <div className="hra-head"><h3>Legal posture</h3></div>
        <ul className="legal-list">
          <li><strong>GDPR (EU 2016/679)</strong> and <strong>Portuguese Law 58/2019</strong>: compliance by
              data minimisation — the platform collects no personal data from visitors; no consent banners are
              needed because there is nothing to consent to. Data-subject requests: contact above.</li>
          <li><strong>ePrivacy (Directive 2002/58/EC)</strong>: no cookies or terminal-equipment access beyond
              strictly functional localStorage.</li>
          <li><strong>EU AI Act (Regulation 2024/1689)</strong>-oriented controls: machine outputs labeled as
              such, human oversight on every consequential action, append-only record-keeping — mapped in the
              public compliance documentation.</li>
          <li>Full documentation:{" "}
            <a href="https://github.com/randorinho/globalpeace/blob/main/docs/COMPLIANCE.md" target="_blank" rel="noreferrer">COMPLIANCE.md</a>,{" "}
            <a href="https://github.com/randorinho/globalpeace/blob/main/docs/GOVERNANCE.md" target="_blank" rel="noreferrer">GOVERNANCE.md</a>.
          </li>
        </ul>
      </div>
    </div>
  );
}
