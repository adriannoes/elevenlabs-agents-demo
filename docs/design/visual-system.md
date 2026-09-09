# Visual System

**Status**: draft
**Scope**: local demo UI only
**Reference**: [ElevenLabs brand guidelines](https://elevenlabs.io/brand)

## Purpose

This document defines a lightweight visual system for the local Gradio demo. The goal is to make
the localhost experience feel polished and aligned with the ElevenLabs ecosystem, while avoiding
any implication that this is an official ElevenLabs product.

The UI should be **brand-inspired**, not **brand-owned**.

## Brand Usage Guardrails

- Use the correct written forms: **ElevenLabs**, **ElevenAgents**, **ElevenAPI**, and
  **ElevenCreative**.
- Do not write `Eleven Labs`, `Eleven Agents`, `Eleven API`, `Elevenlabs`, or all-caps variants.
- Do not recreate the ElevenLabs logo or symbol in text, icons, CSS, ASCII, or custom SVG.
- Do not distort, recolor, rotate, stretch, outline, shadow, or animate official logo assets.
- If official assets are ever used, download them only from the public brand page and keep the
  required clearance around them.
- Prefer text labels over logo usage unless the demo explicitly needs a brand asset.

### Official asset storage

Checked-in copies of downloads from <https://elevenlabs.io/brand> belong under:

- `docs/design/assets/logos/` — wordmarks / full logo lockups
- `docs/design/assets/symbols/` — standalone symbol / icon-only assets

Placement and guardrails stay in this document; keep asset trees clean without extra README noise.

From `apps/gradio_app.py`, resolve paths with:

```python
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DESIGN_ASSETS_DIR = REPO_ROOT / "docs" / "design" / "assets"
BRAND_LOGOS_DIR = DESIGN_ASSETS_DIR / "logos"
BRAND_SYMBOLS_DIR = DESIGN_ASSETS_DIR / "symbols"
```

## Visual Direction

### Global UI

- Minimal, high-contrast layout with generous whitespace.
- Soft surfaces, rounded cards, and restrained motion.
- Clear hierarchy: headline, short context, action, result, evidence.
- Avoid decorative complexity that distracts from voice interaction and metrics.

### ElevenAgents-Inspired Areas

Use this direction for Telecom, Banking, and Healthcare tabs.

- Primary accent: blue family.
- Motifs: circle, sphere, orb, pulse, waveform, status ring.
- Surface: subtle blue gradient over a neutral base.
- Interaction state: "ready", "listening", "responding", "needs setup".
- Copy tone: conversational, clear, and enterprise-ready.

### ElevenAPI-Inspired Areas

Use this direction for TTS Playground, Latency, and Vendor Benchmark tabs.

- Primary palette: monochrome / neutral.
- Motifs: metrics, tables, compact charts, request metadata, headers.
- Surface: clean cards and data panels.
- Interaction state: "request sent", "first byte received", "completed", "skipped".
- Copy tone: technical, concise, and evidence-based.

## Local Design Tokens

These are local demo tokens, not official ElevenLabs brand tokens. If exact official color values
are needed later, confirm them from approved brand assets before naming them as official.

```css
:root {
  --demo-bg: #f7f7f4;
  --demo-surface: #ffffff;
  --demo-surface-muted: #f1f2ef;
  --demo-text: #111111;
  --demo-text-muted: #5f6368;
  --demo-border: #deded8;

  --agents-accent: #2f6df6;
  --agents-accent-soft: #e8f0ff;
  --agents-orb-start: #2f6df6;
  --agents-orb-end: #8fb4ff;

  --api-accent: #111111;
  --api-accent-soft: #eeeeea;
  --success: #168a4a;
  --warning: #b7791f;
  --danger: #c2413a;
}
```

## Component Patterns

### Landing Header

- Title: `ElevenLabs Vertical Exploration`.
- Subtitle: one sentence explaining that this is a local product/engineering exploration.
- Readiness chips:
  - `ElevenLabs key: OK / missing`
  - `OpenAI key: OK / optional / missing`
  - `Agent IDs: configured / pending`
- Links:
  - `README.md`
  - `docs/reports/technical-exploration-report.md`
  - `docs/benchmarks/tts-vendor-comparison.md`

### Scenario Tab

Each scenario tab should include:

- Context card: the business problem.
- Action card: button to start the voice agent widget.
- Evidence card: tools, KB docs, expected outcome, and where to inspect traces.
- Setup card: what is missing if the agent ID or API key is not configured.

### Benchmark Tab

Benchmark tabs should include:

- Input controls on the left.
- Raw runs table.
- Summary metrics: median TTFB, p95 TTFB, mean, total time, sample count.
- Caveat block explaining that latency depends on network, region, provider load, model, and
  output format.

## Accessibility

- Keep sufficient contrast between text and surfaces.
- Do not use color as the only status signal; pair color with text labels.
- Keep controls keyboard-accessible through standard Gradio components.
- Avoid rapid animation or pulsing that could distract from voice playback.

## Implementation Notes

- Keep CSS small and colocated in `apps/gradio_app.py` while the UI remains compact.
- If CSS grows beyond readability, move it to `apps/static/demo.css`.
- Do not commit generated screenshots. For official logos/symbols, only commit files placed under
  `docs/design/assets/logos/` or `docs/design/assets/symbols/` that are needed for the demo and
  compliant with the brand guidelines.
