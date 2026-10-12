# globalpeace.ai — Brandbook

## Identity

**The pulse.** The mark is a globe ring carrying a steady heartbeat: the
platform listens to the world's vital signs and keeps them visible. Calm,
clinical, humane — never alarmist, never martial.

Voice: sober institutional clarity. We state conditions, evidence, and
options; we never rank countries, dramatize suffering, or claim certainty
we don't have.

## Logo

| Asset | File | Use |
|---|---|---|
| Mark | `brand/mark.svg` | Favicons, avatars, compact UI |
| Lockup (light bg) | `brand/logo.svg` | Documents, light surfaces |
| Lockup (dark bg) | `brand/logo-dark.svg` | Site header, dark surfaces |

Rules: ring + pulse are never recolored outside the palette; never rotate,
outline, or add effects; clear space = ring radius on all sides; minimum
size 16 px (mark). The wordmark is Roboto 700, `.ai` in brand green/mint.

## Core palette

| Color | Hex | Role |
|---|---|---|
| Green | `#2B8C72` | Brand primary; human-verified |
| Mint | `#63CDA3` | Soft fills; partially verified; primary on dark |
| Sea-green | `#37675D` | Machine trust (ai_corroborated) |
| Dark slate | `#2A353D` | Ink / dark ground |
| Slate grey | `#41484C` | Muted; not-yet-treated |
| Amber | `#FDAC11` | Alerts & calls to action only |

Full status ladder and accessibility rules: docs/DESIGN.md.

## Conflict-pressure scale (world map)

Measures **situation pressure on vital systems** (HRA vitals: civilian
safety, population stability, food security, health, humanitarian access) —
never country character. Rendered as translucent country halos beneath the
event circles.

| Level | Hex | Threshold (HRA pressure) |
|---|---|---|
| watch | `#7A8C94` | > 0.05 |
| concern | `#C98A2D` | ≥ 0.33 |
| severe | `#B4552D` | ≥ 0.45 |
| alarm | `#8C2F39` | ≥ 0.66 |

Design intent: a warm sequential ramp with strong lightness separation
(legible under color-vision deficiency); it starts at neutral grey-blue so
"watch" never reads as accusation, and deliberately avoids pure red — the
scale signals pressure needing care, not enemies on a war map. Tokens:
`--gp-pressure-*` in `frontend/design/tokens.css`.

## Sharing & app surfaces

- Favicon: the mark (`favicon.svg` + PNG fallbacks 32/180/192/512)
- Link sharing: `og.png` 1200×630 — dark ground, mark + wordmark, mission
  line, trust-ladder footer. Regenerate with the script in git history when
  the mission line changes.
