"""Agentic vetting of a candidate internet source.

Three independent analyst lenses examine a sample of the source's output:
  provenance    — who publishes this? masthead, ownership transparency,
                  editorial standards, contact and correction practices
  integrity     — content quality: fabrication markers, sensationalism,
                  internal consistency, plausibility against institutional
                  reporting of the same situations
  manipulation  — coordinated-inauthenticity signals: synthetic or templated
                  language, impossible sourcing, engagement-bait framing

Promotion doctrine (docs/AUDIT_CRITERIA.md): ALL lenses must independently
recommend `vetted` and none may flag high manipulation risk — otherwise the
source lands in `watch` or `rejected`. Auto-promotion is provisional; a human
ratifies or demotes. Vetting a source never verifies its individual claims.
"""
from __future__ import annotations

import json
import re
import sys
from urllib.parse import urlparse

import httpx

UA = {"user-agent": "globalpeace-ai-pilot/0.1 (source vetting)"}

LENSES = {
    "provenance": "Assess WHO publishes this source: identifiable organisation, masthead, ownership and funding transparency, editorial standards, corrections practice, verifiable contact. Anonymous or untraceable publishers are a serious concern.",
    "integrity": "Assess the CONTENT sample: fabrication markers (unverifiable specifics, non-existent entities), sensationalism vs sourcing, internal contradictions, plausibility against how institutional sources (UN agencies, established datasets) report the same situations.",
    "manipulation": "Assess MANIPULATION signals: templated or synthetic-looking text across items, impossible sourcing chains, engagement-optimised framing, hate or dehumanising language, signs of coordinated narrative pushing.",
}

SCHEMA = {
    "type": "object",
    "properties": {
        "recommendation": {"type": "string", "enum": ["vetted", "watch", "rejected"]},
        "manipulation_risk": {"type": "string", "enum": ["low", "medium", "high"]},
        "fake_news_indicators": {"type": "array", "items": {"type": "string"}},
        "rationale": {"type": "string"},
    },
    "required": ["recommendation", "manipulation_risk", "fake_news_indicators", "rationale"],
    "additionalProperties": False,
}

SYSTEM = """You are one of three independent analysts vetting whether an internet \
source can be trusted as an input to a peace-intelligence platform. You judge the \
SOURCE, not individual claims — vetting never verifies events. Be sceptical: the \
cost of trusting a fabrication mill is far higher than the cost of watching a \
genuine outlet for another month. If evidence is thin, recommend `watch`, not \
`vetted`. Your lens:
"""


BROWSER_UA = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129 Safari/537.36"}


def sample_source(url: str) -> dict:
    """Fetch a small content sample: the page/feed plus item titles.
    Falls back to a browser user-agent for sites that block identified bots
    (read-only sampling for vetting purposes)."""
    r = httpx.get(url, headers=UA, timeout=20, follow_redirects=True)
    if r.status_code in (401, 403, 406):
        r = httpx.get(url, headers=BROWSER_UA, timeout=20, follow_redirects=True)
    r.raise_for_status()
    text = r.text[:60000]

    # Prefer the feed: real article titles + descriptions beat JS-era homepages.
    feed_text = ""
    if "<rss" not in text[:2000] and "<feed" not in text[:2000]:
        base = str(r.url).rstrip("/")
        for path in ("/feed", "/feed/", "/rss.xml", "/rss", "/atom.xml"):
            try:
                fr = httpx.get(base + path, headers=BROWSER_UA, timeout=15, follow_redirects=True)
                if fr.status_code == 200 and ("<rss" in fr.text[:2000] or "<feed" in fr.text[:2000]):
                    feed_text = fr.text[:60000]
                    break
            except httpx.HTTPError:
                continue
    else:
        feed_text = text

    src = feed_text or text
    titles = re.findall(r"<title>(?:<!\[CDATA\[)?([^<\]]{5,200})", src)[:25]
    descriptions = re.findall(r"<description>(?:<!\[CDATA\[)?([^<\]]{20,500})", src)[:15]
    body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"\s+", " ", body).strip()[:4000]
    return {"url": url, "domain": urlparse(str(r.url)).hostname, "titles": titles,
            "item_descriptions": descriptions, "body_sample": body,
            "sampled_from": "feed" if feed_text else "page"}


def vet(url: str) -> dict:
    import anthropic

    sample = sample_source(url)
    client = anthropic.Anthropic()
    opinions: dict[str, dict] = {}
    for lens, lens_text in LENSES.items():
        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=2048,
            system=SYSTEM + lens_text,
            output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content": "Source sample:\n" + json.dumps(sample, indent=1)[:30000]}],
        )
        if response.stop_reason == "refusal":
            opinions[lens] = {"recommendation": "watch", "manipulation_risk": "medium",
                              "fake_news_indicators": ["analyst declined"], "rationale": "refusal"}
            continue
        opinions[lens] = json.loads(next(b.text for b in response.content if b.type == "text"))

    recs = [o["recommendation"] for o in opinions.values()]
    risks = [o["manipulation_risk"] for o in opinions.values()]
    if any(r == "rejected" for r in recs) or "high" in risks:
        verdict = "rejected" if any(r == "rejected" for r in recs) else "watch"
    elif all(r == "vetted" for r in recs):
        verdict = "vetted"  # unanimous panel -> provisional promotion
    else:
        verdict = "watch"

    return {
        "domain": sample["domain"],
        "verdict": verdict,
        "status": "provisional",  # human ratifies in the registry
        "unanimous": all(r == recs[0] for r in recs),
        "opinions": opinions,
        "model": "claude-opus-5",
    }
