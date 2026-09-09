# Tech Stack Decisions

This document records the approved technology choices for the `eleven-demo` repository, with the trade-offs that led to each choice. PRDs and tasks reference this file; do not propose changes without a matching ADR-style update here first.

## Summary

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.13 | Latest stable, broad library support, ElevenLabs SDK is Python-first. |
| Package manager | uv | Fast resolver, single binary, lockfile reproducibility, modern (Astral). |
| Data validation | Pydantic v2 | De-facto standard for Python typed data; SDK already uses it. |
| Settings | pydantic-settings | Typed env loading, validation at startup. |
| HTTP client | httpx (transitive) | Async-first, used by the ElevenLabs SDK internally. |
| WebSocket client | websockets | Reference Python implementation, asyncio-native. |
| Demo UI | Gradio | Fastest path to a polished AI demo with audio I/O; minutes to add a tab. |
| Backend service | FastAPI (minimal) | Used only for the WebSocket bridge demo. ASGI native, plays well with `websockets`. |
| MCP (lab) | `mcp` v2 `MCPServer` stdio | One mock tool (`lookup_telecom_account`). Not the hosted ElevenLabs MCP (`/v1/mcp`). |
| ASGI server | Uvicorn | Standard pair for FastAPI. |
| CLI output | rich | Pretty tables and progress bars without HTML overhead. |
| Linting + formatting | ruff | Replaces flake8, isort, black, pylint; single tool, 10-100x faster. |
| Type checking | mypy (strict) | Strict for `src/`, relaxed for `tests/` and `scripts/`. |
| Test runner | pytest | Industry standard. |
| Async tests | pytest-asyncio | `asyncio_mode = "auto"`. |
| Parallel tests | pytest-xdist | Fast unit loop with `-n auto`. |
| HTTP recording | pytest-vcr (vcrpy) | Records ElevenLabs API responses once; replayed locally. CI runs unit tests only. |
| Coverage | pytest-cov | Single dedicated invocation (no xdist) per the testing-standards rule. |
| Pre-commit | pre-commit + ruff + gitleaks + detect-private-key | Catches lints and secrets before commit. |

## Decision details and rejected alternatives

### UI framework: Gradio (primary) + minimal Next.js reference surface (stretch)

- **Gradio (primary)**: ~30 lines for a working multi-tab demo with audio in/out. ElevenLabs ships Gradio examples in their docs. This is the surface that exercises every vertical (TTS Playground, three agents, latency, vendor benchmark) end-to-end against the live platform.
- **Streamlit (rejected)**: equally fast for dashboards, weaker on audio I/O, harder to embed external widgets like the ElevenLabs JS SDK.
- **Next.js as full replacement (rejected)**: best polish, but adds a TypeScript codebase, build step, and ~10x more setup cost. Out of scope as the *primary* exploration surface.
- **Next.js as small reference surface (accepted, stretch — Task 6.7)**: a single page under `apps/web/` using the official [`elevenlabs/ui`](https://github.com/elevenlabs/ui) registry (`Orb`, `ConversationBar`, `LiveWaveform`) wired to `DEMO_AGENT_ID_TELECOM` via `@elevenlabs/react`. Same agent that the Python `scripts/agent_create.py telecom` provisions. Signed URLs are minted by `app/api/signed-url/route.ts` with `@elevenlabs/elevenlabs-js`, keeping API keys server-side without rewriting the Python exploration in TypeScript.

Demo-local UI tokens and brand guardrails: [`docs/design/visual-system.md`](../../docs/design/visual-system.md).
Official logo/symbol files (when committed): **`docs/design/assets/logos/`** and **`docs/design/assets/symbols/`**.

### Lab MCP server vs hosted ElevenLabs MCP

- **This repo** ships a stdio `MCPServer` process (`scripts/mcp_telecom.py`, `mcp` SDK v2) that wraps the existing telecom mock. Purpose: feel MCP tool attachment without OAuth or a public URL.
- **Hosted ElevenLabs MCP** (`https://api.elevenlabs.io/v1/mcp`) manages workspace agents from Claude/Cursor. Out of scope to reimplement; documented in `docs/mcp-lab-server.md`.
- **Archived `elevenlabs/elevenlabs-mcp`** (2026-08-20) is not vendored.

### Multi-stack by design (Python primary, Node-only secondary surface)

- **Primary surface**: Python (uv, Gradio). Covers exploration, CLIs, scenarios, KB / RAG, benchmarks, and integration tests with VCR cassettes.
- **Secondary surface (stretch)**: Node 20+ / pnpm under `apps/web/`, fully isolated. Exists only to exercise the official `elevenlabs/ui` registry on top of the same agent provisioned by Python.
- **Toolchain isolation**: `apps/web/` ships its own `package.json`, `pnpm-lock.yaml`, and `node_modules/`. It does **not** appear in `pyproject.toml`, `uv.lock`, the Python pre-commit hooks, or the Python quality gates in Task 8.0. Lint / build of the Node surface is verified manually by the developer; failures there do not block the Python release run.
- **Shared contract**: the Node surface and the Python surface share **only environment variable names** (`ELEVENLABS_API_KEY`, `DEMO_AGENT_ID_TELECOM`). They do not share code, schemas, or runtime processes.

### `elevenlabs/ui` evaluation

- **Source**: <https://github.com/elevenlabs/ui> — a custom shadcn/ui registry maintained by the ElevenLabs team for React / Next.js applications.
- **Components considered**: `orb`, `conversation`, `conversation-bar`, `message`, `transcript-viewer`, `live-waveform`, `waveform`, `voice-button`, `voice-picker`, `mic-selector`, `audio-player`, `scrub-bar`, `speech-input`, `response`, `shimmering-text`, `bar-visualizer`, `matrix`.
- **Shipped dependencies**: `@elevenlabs/react`, `@elevenlabs/elevenlabs-js`, `three`, `@react-three/fiber`, `@react-three/drei`, `lucide-react`, shadcn/ui, Tailwind CSS, Next.js 14, Node 20+. `framer-motion` was considered through the registry ecosystem but is not currently required by the shipped page.
- **Decision**: adopt as a stretch reference surface (Task 6.7) rather than as a replacement for the Python lab. Rationale:
  - The registry covers the *front-end* of an agent-driven product. It does not provision agents, upload knowledge bases, compute RAG, run TTFB benchmarks, or back integration tests with cassettes — all of which remain Python-first via the official `elevenlabs-python` SDK.
  - Migrating the existing Python work to TypeScript would discard the breadth of platform coverage already shipped (Tasks 1.0–6.1) for little gain beyond a single conversation UI.
  - Using `elevenlabs/ui` for one focused page documents a typical customer Next.js integration while keeping the rest of the exploration Python-first.
- **Documentation flow**: the registry is referenced from `apps/web/README.md`, cross-linked from `docs/walkthrough.md` (Task 7.4), captured in `docs/reports/technical-exploration-report.md` (Task 7.8), and may be summarized in optional learning notes or Task 7.9.

**Rejected alternatives** (UI tier): Streamlit, Reflex, full Next.js port of every Gradio tab.

### Package manager: uv (chosen) vs pip vs Poetry

- **uv**: 10-100x faster than pip; single static binary; deterministic lockfile.
- **pip**: ubiquitous but slow, no lockfile by default, dependency resolution can be brittle.
- **Poetry**: solid lockfile, but slower and heavier than uv.

**Rejected alternatives**: pip-tools, Poetry, Hatch CLI.

### TTS model selection (default): `eleven_flash_v2_5`

- **Flash v2.5**: lowest TTFB (~75-150 ms), good enough quality for conversational demos, supports Brazilian Portuguese.
- **Multilingual v2**: higher quality, significantly higher latency. Use for the Healthcare scenario and Voice Library exploration.
- **v3**: most expressive (tags, emotion). Use for marketing-style demos in the TTS Playground tab.
- **English Convai agents**: `eleven_flash_v2` (Convai accepts flash_v2 / turbo_v2 for English; Turbo is deprecated on the Models page).

Pinned in `.env.example`; per-call overrides allowed.

### Output format default: `mp3_22050_32`

- Smallest payload that still sounds clean for voice. Halves bandwidth vs `mp3_44100_128` and meaningfully reduces perceived TTFB.

### Test recording: VCR cassettes (chosen) vs pure mocks

- **VCR**: real-shape responses, future-proof against SDK changes. One-time recording cost (a few credits).
- **Pure mocks**: zero credits but tend to drift from reality and miss real bugs.

**Rule**: integration tests use VCR; unit tests use pure mocks.

### Async vs sync ElevenLabs SDK calls

- **Sync**: scripts and unit tests. Easier to read and debug.
- **Async (`websockets` directly)**: only for streaming TTS, STT realtime, and Agents conversation WebSocket.

The `eleven_demo.client` module exposes both surfaces from the same factory.

### Post-call analysis without an HTTP webhook receiver

- **Chosen**: Operational exploration uses `get_client().conversational_ai.conversations.list` / `get` through `scripts/conversations_list.py` when needed. The CLI prints redacted conversation IDs, status, success, duration, message counts, and analysis summaries so local demos can inspect recent calls without storing raw transcripts in repo artifacts.
- **Rejected for this repo**: Running a dedicated HTTP endpoint for [post-call webhooks](https://elevenlabs.io/docs/eleven-agents/workflows/post-call-webhooks) — adds deployment surface (TLS, signature verification, uptime, signature validation, and PII redaction) beyond the demo scope while providing marginal benefit for local exploration.

Document webhook flows in narrative docs so production integrations remain discussable without implementing them here. See [`docs/patterns/post-call-webhooks.md`](../../docs/patterns/post-call-webhooks.md) for a concise checklist. If a production-style system needs durable call records, build a separate authenticated webhook receiver with signature verification and redaction instead of extending this local lab.

## Out of scope (explicit non-goals)

- TypeScript / Next.js / React as the **primary** exploration surface. A small reference surface under `apps/web/` (Task 6.7) using the official `elevenlabs/ui` registry is allowed and desirable.
- Mobile (iOS / Android / React Native).
- Real telephony (Twilio / SIP / Plivo / Vonage). The Gradio app simulates the conversation surface; integration is documented but not wired.
- Voice biometrics. Mentioned as a talking point for Banking, not implemented.
- Multi-tenant production deployment. Single-developer local exploration.
- Running Node lint / test / build inside the Python pre-commit or quality gates. Toolchains stay isolated.

## Update process

1. Open a PR titled `chore(architecture): adjust tech-stack — <change>`.
2. Update this file with rationale and rejected alternatives.
3. Update `pyproject.toml` and `uv.lock` in the same PR.
4. If the change affects a generated PRD or task list, regenerate it.
