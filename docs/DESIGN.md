# Design System

## Typeface

**Roboto** — https://fonts.google.com/specimen/Roboto (weights 400 / 500 / 700;
Roboto Mono for data/code). **Self-host** the woff2 files in production rather
than hotlinking Google Fonts: no third-party request (privacy — fits
GOVERNANCE.md data-minimisation), and it keeps working under a strict CSP.

## Palette

| Swatch | Hex | Role |
|---|---|---|
| Amber | `#FDAC11` | Alerts, calls to action, `disputed` status — always with dark ink on top |
| Dark slate | `#2A353D` | Ink (light theme) / background (dark theme) |
| Green | `#2B8C72` | Primary brand: actions, links, `verified` status |
| Mint | `#63CDA3` | Soft fills, hovers, `partially_verified`; primary on dark |
| Slate grey | `#41484C` | Muted text, `unverified` status, dark-theme surfaces |

Tokens live in [`frontend/design/tokens.css`](../frontend/design/tokens.css) —
semantic variables (`--gp-primary`, `--gp-alert`, …), never raw hexes in components.

## Accessibility notes

- White text on `#2B8C72` passes AA for large text only — use white on green for
  buttons ≥ 16 px bold, otherwise dark ink on mint.
- `#FDAC11` fails contrast with white: amber elements always take `#2A353D` ink.
- Mint `#63CDA3` is the primary on dark backgrounds (green recedes on slate).
- Status colors must never be the only signal (color-blind users): pair with the
  status label text or an icon.

## Tone

The platform reports violence and humanitarian harm. The palette is deliberately
calm — green/mint ground, amber reserved for genuine alerts. Never use red-vs-green
"good country / bad country" coding (see DATA_MODEL.md: no villain rankings).
