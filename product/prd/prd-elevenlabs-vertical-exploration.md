# PRD — ElevenLabs Vertical Exploration

**Status**: draft
**Owner**: Adrianno
**Last updated**: 2026-04-30
**Related documents**:
- [README.md](../../README.md)
- [engineering/architecture/tech-stack-decisions.md](../../engineering/architecture/tech-stack-decisions.md)
- [engineering/tasks/tasks-prd-elevenlabs-vertical-exploration.md](../../engineering/tasks/tasks-prd-elevenlabs-vertical-exploration.md) — post-delivery summary and verification pointers (canonical task checklist).
- **`docs/design/assets/logos/`**, **`docs/design/assets/symbols/`** — Checked-in official SVG/PNG from [elevenlabs.io/brand](https://elevenlabs.io/brand); placement and guardrails in [docs/design/visual-system.md](../../docs/design/visual-system.md).
- [Demo agent setup (Portuguese)](../guides/demo-agent-setup.md) — provisioning via API and `DEMO_AGENT_ID_*` variables.

## 1. Introduction / Overview

`eleven-demo` is a small Python repository for hands-on exploration of [ElevenAgents](https://elevenlabs.io/docs/eleven-agents/overview) and [ElevenAPI](https://elevenlabs.io/docs/api-reference/introduction) through three Brazilian-market scenarios: Telecom, Banking, and Healthcare, plus a focused TTS vendor benchmark. The goal is to build product intuition fast — what to use, when, with what trade-offs — by shipping three thin verticals end-to-end on the platform and instrumenting the core voice-generation path.

The repository is structured so that each capability (TTS, STT, voices, agents, knowledge base, latency measurement) is exercised as an isolated CLI script first, then composed into a Gradio multi-vertical demo, and finally wrapped (where useful) by a minimal FastAPI surface for production-style discussions.

## 2. Goals

1. **Cover the platform's most consequential primitives**: synchronous and streaming TTS, batch and realtime STT, voice catalog filtering, agent CRUD, server / system tools, knowledge base + RAG, simulated conversations, post-call analysis, latency measurement.
2. **Ship three vertical demos that feel real for the Brazilian market**: Telecom SAC, Banking digital-bank CX, Healthcare triage. Each runs end-to-end against the live ElevenLabs platform from `apps/gradio_app.py`.
3. **Add a focused vendor benchmark for TTS latency**: compare ElevenLabs Flash v2.5 streaming against OpenAI `gpt-4o-mini-tts` streaming for short PT-BR customer-service utterances, using TTFB as the primary metric and total generation time as a secondary metric.
4. **Keep engineering discipline tight**: every change is an atomic Conventional Commit, every module has unit tests, integration tests use VCR cassettes for deterministic CI, ruff and pre-commit hooks gate everything.
5. **Make every architectural decision explicit and revisitable**: PRD, tech-stack ADR, scenario docs, benchmark docs, and skills are first-class artifacts, not afterthoughts.
6. **Use the official SDK and project skills intentionally**: rely on `elevenlabs-docs`, `elevenlabs-agents`, and `elevenlabs-api-cookbook`, plus the task decomposition in `engineering/tasks/`, so each step stays traceable to docs and repeatable.

## 3. User Stories

The primary audience is a developer cloning the repo to learn ElevenLabs; the docs are structured so collaborators can onboard without tribal context.

- **As a developer exploring the ElevenLabs platform**, I want a single command that opens a multi-tab UI showing TTS, three voice agents, and a live latency benchmark, so I can probe the platform interactively without writing UI code.
- **As a developer comparing TTS models**, I want a CLI that runs N TTS Flash and N TTS Multilingual calls and prints a TTFB table with median and p95, so I can build evidence-based intuition about latency budgets.
- **As a developer comparing TTS vendors**, I want a reproducible benchmark that runs the same short PT-BR utterances through ElevenLabs Flash v2.5 and OpenAI `gpt-4o-mini-tts`, so I can reason about latency, output format, ergonomics, and use-case fit with measured evidence.
- **As a developer designing a vertical**, I want each scenario declared as a Python configuration object with `SYSTEM_PROMPT`, `FIRST_MESSAGE`, `LANGUAGE`, `TOOL_NAMES`, `KB_IDS`, `SUCCESS_CRITERIA`, a `provision()` function, and `voice_id` on `Scenario` (resolved via `from_settings()`), so I can iterate on prompts without touching demo code (`TOOL_NAMES` map to server-tool mocks; `KB_IDS` lists knowledge-base document IDs after upload for Healthcare).
- **As a developer writing tests**, I want unit tests to mock the SDK and integration tests to replay VCR cassettes, so CI runs in seconds and never burns API credits.
- **As a developer extending the repo**, I want clear skills, rules, and templates so my AI assistant follows the same conventions on every new feature.
- **As a teammate opening the repo for the first time**, I want a README that gets me from clone to running demo in under five minutes.

## 4. Functional Requirements

### 4.1 Library — `src/eleven_demo/`

- **FR-1**: `eleven_demo.client.get_client()` returns a configured `ElevenLabs` SDK client. Retry (3 attempts, exponential backoff) on HTTP 429 and 5xx applies to synchronous REST/SDK traffic — implemented via the SDK’s configurable HTTP transport or thin wrappers so callers do not bypass retries accidentally. All other modules import only this factory.
- **FR-2**: `eleven_demo.config.Settings` (pydantic-settings) reads `ELEVENLABS_API_KEY`, `OPENAI_API_KEY` (optional; only required for the vendor benchmark), `DEFAULT_PT_VOICE_ID`, `DEFAULT_EN_VOICE_ID`, `DEMO_AGENT_ID_*`, `TTS_MODEL_ID`, `TTS_OUTPUT_FORMAT`, `STT_MODEL_ID`, `STT_REALTIME_MODEL_ID`, `OPENAI_TTS_MODEL_ID`, `OPENAI_TTS_VOICE`, `OPENAI_TTS_RESPONSE_FORMAT`, `LOG_LEVEL` from `.env`. Required fields fail fast at startup; optional vendor fields skip gracefully when unset.
- **FR-3**: `eleven_demo.tts.sync.synthesize(text, voice_id, model_id, output_format) -> tuple[bytes, dict]` returns concatenated audio and a metadata dict (`character_count`, `request_id`, `model_id`, …) from `with_raw_response` headers for cost/traceability.
- **FR-4**: `eleven_demo.tts.stream.stream(text, voice_id, ...) -> Iterator[tuple[bytes, float | None]]` yields `(chunk, ttfb_seconds)` where `ttfb_seconds` is set only on the first chunk (HTTP chunked streaming); alternatively callers may wrap iteration with `measure_ttfb` from FR-9 for aggregate stats.
- **FR-5**: `eleven_demo.tts.ws.ws_stream(text_chunks, voice_id, ...)` is an async generator that uses the TTS WebSocket and yields audio bytes as they arrive.
- **FR-6**: `eleven_demo.stt.batch.transcribe(file_path, language="por") -> Transcript` returns text with diarization and audio events when supported.
- **FR-7**: `eleven_demo.stt.realtime.realtime_transcribe(audio_chunks)` is an async generator yielding partial and committed transcripts via the STT realtime WebSocket; default realtime model ID is `scribe_v2_realtime` (confirm against [Models](https://elevenlabs.io/docs/overview/models) when pinning).
- **FR-8**: `eleven_demo.voices.catalog.list_pt_br_voices() -> list[VoiceCard]` filters Voice Library voices for Brazilian Portuguese.
- **FR-9**: `eleven_demo.metrics.latency.measure_ttfb` is a decorator and `LatencyReport(median, p95, mean, samples)` summarizes a series of measurements.
- **FR-10**: `eleven_demo.agents.factory` exposes idempotent `create_agent`, `update_agent`, `delete_agent`, `list_agents`. Lookups are by name.
- **FR-11**: `eleven_demo.agents.tools` defines Pydantic schemas and mock implementations for `lookup_telecom_account(cpf)`, `lookup_account_summary(cpf)`, `request_card_block(card_id, reason)`, `request_card_replacement(reason)`, `book_medical_appointment(specialty, date, patient_id)`, `transfer_to_human(reason)`.
- **FR-12**: `eleven_demo.agents.kb` provides `upload_kb_text`, `upload_kb_file`, `compute_rag(doc_ids)` for the Healthcare scenario.
- **FR-13**: `eleven_demo.agents.simulate.simulate(agent_id, user_messages)` returns a `SimulationResult` with the transcript, tool calls, and analysis output.
- **FR-14**: `eleven_demo.scenarios.{telecom,banking,healthcare}` each export `SYSTEM_PROMPT`, `FIRST_MESSAGE`, `LANGUAGE`, `TOOL_NAMES`, `KB_IDS`, `SUCCESS_CRITERIA`, and `provision() -> agent_id`. Voice lives on `Scenario.voice_id`, set by `from_settings()` (not a module-level `VOICE_ID` constant, so modules import without `Settings`).

### 4.2 CLI scripts — `scripts/`

- **FR-15**: `tts_demo.py "<text>"` writes `out.mp3` and prints character cost from raw response headers.
- **FR-16**: `tts_stream_ttfb.py [--n N] [--model flash|multilingual]` prints a TTFB table with median and p95.
- **FR-17**: `stt_demo.py <audio>` prints the transcript with speaker labels.
- **FR-18**: `voices_pt_br.py` prints a `rich` table of Brazilian Portuguese voices.
- **FR-19**: `agent_create.py <telecom|banking|healthcare>` provisions or updates the scenario's agent and prints the resulting `agent_id`.
- **FR-20**: `agent_simulate.py <scenario> "<message>"` runs a simulated conversation and prints the analysis (`call_successful`, `transcript_summary`).

### 4.2.1 Vendor benchmark — `src/eleven_demo/benchmarks/` and `scripts/`

- **FR-31**: `eleven_demo.benchmarks.tts_vendor` defines a `VendorSample` model and a `VendorBenchmarkReport` model with provider, model, voice, output format, region/header metadata where available, per-run TTFB, total generation time, byte count, and summary stats (median, p95, mean).
- **FR-32**: `eleven_demo.benchmarks.openai_tts.stream_openai_tts(...)` streams OpenAI TTS using `OPENAI_API_KEY`, defaulting to `gpt-4o-mini-tts`, `voice="coral"`, and `response_format="mp3"` for the apples-to-apples browser-playback baseline. Optional `response_format="pcm"` is supported as an OpenAI fastest-path control, but it is not the headline comparison.
- **FR-33**: `scripts/tts_vendor_benchmark.py` runs N ElevenLabs streaming calls and N OpenAI streaming calls over the same short PT-BR utterance set, randomizes provider order to reduce warm-cache bias, prints a `rich` table, and writes `artifacts/benchmarks/tts-vendor-latest.json`.
- **FR-34**: The benchmark's primary hypothesis is contextual, not universal: for short interactive PT-BR utterances with compressed browser-friendly audio, ElevenLabs Flash v2.5 should produce lower TTFB than OpenAI `gpt-4o-mini-tts`. If a run does not support that hypothesis, the report must preserve the raw numbers instead of hiding them.
- **FR-35**: `docs/benchmarks/tts-vendor-comparison.md` explains the methodology, caveats, exact prompts, model IDs, output formats, local network context, and how to rerun the benchmark.

### 4.3 Demo apps — `apps/`

- **FR-21**: `apps/gradio_app.py` exposes six tabs: TTS Playground, Telecom, Banking, Healthcare, Latency, Vendor Benchmark. Each agent tab uses a signed URL to embed the official ElevenLabs voice widget. The TTS Playground uses `gr.Audio(autoplay=True)` per §6.1. Agent tabs rely on the embedded widget for conversation UI; server-tool traces are visible via ElevenLabs dashboard / post-call analysis workflows ([Agent Testing](https://elevenlabs.io/docs/eleven-agents/customization/agent-testing)), not as a separate Gradio-native trace viewer unless explicitly added later.
- **FR-22**: The Latency tab runs 10 streaming TTS calls (Flash by default) and shows a live TTFB chart and a summary table.
- **FR-22a**: The Vendor Benchmark tab runs the same benchmark as `scripts/tts_vendor_benchmark.py` when `OPENAI_API_KEY` is present; otherwise it shows setup instructions and keeps the rest of the app usable.
- **FR-23 (stretch — first to descope if time runs short)**: `apps/ws_bridge/main.py` is a FastAPI service with `/ws/tts` (proxy to ElevenLabs TTS WebSocket) and `/healthz`. Intended for **local development only**: no authentication on `/ws/tts`; production deployments must add auth, TLS, and rate limiting — never expose this bridge directly to the public internet as-is.
- **FR-23a (stretch — priority over FR-23)**: `apps/web/` is a minimal Next.js 14 (App Router) application that uses the official [`elevenlabs/ui`](https://github.com/elevenlabs/ui) registry to render `Orb`, `ConversationBar`, and `LiveWaveform` connected to `DEMO_AGENT_ID_TELECOM` via the `useConversation` hook from `@elevenlabs/react`. Signed URLs are minted server-side in `app/api/signed-url/route.ts` so the raw `ELEVENLABS_API_KEY` never reaches the browser. The Node toolchain (pnpm, `node_modules/`, `.next/`) lives entirely under `apps/web/` and does not affect Python tooling. Same agent provisioned by `scripts/agent_create.py telecom` powers both this React surface and the Gradio Telecom tab — the two surfaces interoperate through a shared `agent_id`, not shared code.

### 4.4 Tests — `tests/`

- **FR-24**: Unit tests under `tests/unit/` mock the SDK and assert on shape, not on byte counts. Coverage target: 80% on `src/eleven_demo/`.
- **FR-25**: Integration tests under `tests/integration/` use `pytest-vcr` cassettes filtered to strip `xi-api-key`. Marked `@pytest.mark.integration`. CI replays cassette-backed tests with a placeholder key (no live secret). Tests skip when `ELEVENLABS_API_KEY` is unset and no cassette is present.
- **FR-26**: Each scenario has at least one regression test that runs `simulate` with a canonical 3-turn conversation and asserts on `SUCCESS_CRITERIA`.

### 4.5 Tooling and docs

- **FR-27**: `uv` manages dependencies; `uv.lock` is committed.
- **FR-28**: `ruff` lints and formats; pre-commit runs ruff + gitleaks + detect-private-key on every commit.
- **FR-29**: `README.md` covers architecture, three verticals, tech-stack trade-offs, demo map, project structure, and a setup that completes in under five minutes.
- **FR-30**: Every scenario has a storytelling document under `docs/scenarios/` (persona, problem, demo flow, ROI hypothesis, talking points, risks).
- **FR-36**: `docs/reports/technical-exploration-report.md` summarizes the exploration as a readable technical report: executive summary, architecture, demo portfolio, benchmark results, testing evidence, product insights, risks, and next steps.
- **FR-37**: Release-quality commands generate evidence artifacts under `artifacts/reports/`: `pytest.xml`, coverage terminal output / XML / HTML, pre-commit output, and the latest vendor benchmark JSON. These artifacts support the report but must not contain secrets or raw PII.

## 5. Non-Goals (Out of Scope)

- TypeScript / Next.js / React as the **primary** exploration surface. A small reference surface under `apps/web/` (FR-23a, Task 6.7) using the official [`elevenlabs/ui`](https://github.com/elevenlabs/ui) registry is allowed and desirable as a stretch deliverable — it complements (does not replace) the Gradio app.
- Re-implementing scenarios, knowledge base, RAG, benchmarks, or integration tests in TypeScript. The `apps/web/` surface consumes a single Python-provisioned agent and renders one conversation page; provisioning and platform CRUD remain Python-first.
- Running Node lint / test / build inside the Python pre-commit, the Python quality gates (Task 8.0), or the Python coverage target. The two toolchains coexist but stay isolated.
- Mobile applications (iOS / Android / React Native).
- Real telephony integration (Twilio / SIP / Plivo / Vonage). The Gradio app is the simulated conversation surface.
- Blanket vendor-ranking claims. The benchmark is scoped to short PT-BR streaming TTS from the developer's local environment and must report measured results transparently.
- Voice biometrics. Mentioned as a Banking talking point; not implemented.
- Multi-tenant production deployment, K8s manifests, Terraform, observability stack.
- Localization beyond Brazilian Portuguese and English.
- Real customer data of any kind. All scenarios use fictional companies and synthetic data.

## 6. Design Considerations

### 6.1 Gradio aesthetic

- Default Soft theme with light custom CSS allowed when it improves demo clarity.
- Visual direction is inspired by the official ElevenLabs brand system, but the app must not look like an official ElevenLabs product unless brand assets are used exactly as permitted by the [brand guidelines](https://elevenlabs.io/brand).
- Local UI tokens, component patterns, and brand-usage guardrails are documented in [docs/design/visual-system.md](../../docs/design/visual-system.md). These are demo-local tokens, not official ElevenLabs design tokens.
- Official logo/symbol files (when used) live under **`docs/design/assets/logos/`** or **`docs/design/assets/symbols/`**, not recreated in CSS or custom SVG.
- Use correct platform names in UI copy: **ElevenAgents** and **ElevenAPI**.
- For the voice-agent tabs, lean into the ElevenAgents visual language: blue accents, soft gradients, circular / orb-like status elements, and generous whitespace.
- For API / benchmark tabs, lean into the ElevenAPI visual language: monochrome / neutral palette, crisp tables, kinetic-metric feel, and minimal decoration.
- Do not recreate, distort, recolor, rotate, add effects to, or approximate ElevenLabs logos / symbols. If a logo is used, keep required clearance and use official assets only.
- Each tab has a left panel (controls) and a right panel (output + context). The right panel includes a small "Why this matters" callout per scenario.
- Audio output uses `gr.Audio(autoplay=True)` for instant feedback.
- Latency tab uses `gr.LinePlot` for the live TTFB series.

### 6.2 CLI output

- `rich.console.Console` for tables and panels.
- `rich.progress.Progress` for any operation longer than 2 seconds.
- All scripts accept `--help` (Typer or argparse with sane defaults).

### 6.3 Evidence report

- The primary human-readable artifact is `docs/reports/technical-exploration-report.md`.
- Generated machine-readable evidence lives under `artifacts/reports/` and `artifacts/benchmarks/`.
- The report must be written in English and framed as a product/engineering exploration of the APIs—not as marketing copy or a superficial vendor pitch.
- Metrics are summarized with caveats; raw benchmark numbers are preserved instead of cherry-picked.

## 7. Technical Considerations

- **Approved stack**: see [engineering/architecture/tech-stack-decisions.md](../../engineering/architecture/tech-stack-decisions.md).
- **Cursor skills**: the assistant uses `[elevenlabs-docs](../../.cursor/skills/elevenlabs-docs/SKILL.md)`, `[elevenlabs-agents](../../.cursor/skills/elevenlabs-agents/SKILL.md)`, `[elevenlabs-api-cookbook](../../.cursor/skills/elevenlabs-api-cookbook/SKILL.md)` to fetch authoritative ElevenLabs context.
- **Cursor rules**: project-wide rules in `.cursor/rules/` enforce SOLID, Python style, security, testing, commits, and ElevenLabs SDK conventions.
- **Model selection**: defaults pinned in `.env.example` (`eleven_flash_v2_5` for TTS, `mp3_22050_32` for output, `scribe_v2` for batch STT, `scribe_v2_realtime` for realtime STT per [Models](https://elevenlabs.io/docs/overview/models)). Per-call overrides allowed.
- **Vendor benchmark design**: the primary benchmark compares ElevenLabs `eleven_flash_v2_5` streaming (`mp3_22050_32`) against OpenAI `gpt-4o-mini-tts` streaming (`response_format="mp3"`) on the same short PT-BR customer-service utterances. This deliberately targets the interactive voice-agent path where ElevenLabs Flash is designed to perform well ([Models](https://elevenlabs.io/docs/overview/models), [Latency optimization](https://elevenlabs.io/docs/eleven-api/guides/how-to/best-practices/latency-optimization)). OpenAI `pcm` may be included as a secondary fastest-path control, documented separately so the headline comparison remains readable.
- **Benchmark caveat**: TTFB depends on local network, routing, provider region, output format, model load, and voice selection. The repo should show raw data, environment notes, and rerun instructions rather than hard-coding a winner.
- **Compliance posture**: scenarios that touch PII (Banking, Healthcare) must enable Zero Retention Mode and document the choice in their docstring.
- **Telecom escalation**: demos use the mocked server tool `transfer_to_human(reason)`. Production carrier integrations typically use the platform **transfer_to_number** system tool ([Transfer to number](https://elevenlabs.io/docs/eleven-agents/customization/tools/system-tools/transfer-to-number)); real PSTN/SIP wiring stays out of scope (Non-Goals §5).
- **Idempotency**: `scenario.provision()` must update an existing agent in place when one matches by name.
- **Cost control**: integration tests record VCR cassettes once; CI replays them. Live API access is limited to local development and recording sessions.
- **Reportability**: every final verification command should either update a reportable artifact (`pytest.xml`, coverage, benchmark JSON) or be referenced in the final technical report. Generated artifacts must redact API keys, authorization headers, request payloads containing PII, and any local-only secrets.
- **Reference UI registry**: [`elevenlabs/ui`](https://github.com/elevenlabs/ui); Gradio aligns with its conversation state semantics in `docs/design/visual-system.md`. `apps/web/` (FR-23a) adds a minimal Next.js + signed-URL example. Details: [`elevenlabs/ui` evaluation](../../engineering/architecture/tech-stack-decisions.md#elevenlabsui-evaluation) in tech-stack-decisions.
- **Multi-stack isolation**: the Node toolchain for `apps/web/` is fully scoped to that directory (`package.json`, `pnpm-lock.yaml`, `node_modules/`, `.next/`). It must not leak into `pyproject.toml`, `uv.lock`, `.pre-commit-config.yaml`, or the quality-gate commands in PRD §Success Metrics.

## 8. Success Metrics

The exploration is complete when all of the following are true:

- [ ] `uv run gradio apps/gradio_app.py` opens cleanly and all six tabs respond.
- [ ] `uv run pytest -n auto` passes (unit and integration via VCR), with at least 80% coverage on `src/eleven_demo/` (verify with `uv run pytest --cov=src/eleven_demo --cov-report=term --cov-fail-under=80 -m "not integration"` per `.cursor/rules/testing-standards.mdc`).
- [ ] Three scenario regression tests (`telecom`, `banking`, `healthcare`) pass via simulated conversations.
- [ ] The Latency tab and `scripts/tts_stream_ttfb.py` reproduce reasonable TTFB ranges (Flash median under 250 ms from a Brazilian connection; document actual numbers in `docs/scenarios/`).
- [ ] The Vendor Benchmark tab and `scripts/tts_vendor_benchmark.py` produce a reproducible ElevenLabs vs OpenAI TTS comparison report, with ElevenLabs Flash v2.5 measured as the primary low-latency hypothesis and raw OpenAI results preserved.
- [ ] `git log --oneline` shows Conventional Commits, atomic, ~300 lines per commit.
- [ ] `pre-commit run --all-files` is clean.
- [ ] README walks a new reader through setup in under five minutes.
- [ ] `docs/walkthrough.md` exists and covers every demo from start to finish.
- [ ] Each vertical has a one-page storytelling document in `docs/scenarios/`.
- [ ] `docs/reports/technical-exploration-report.md` exists and can be read independently before opening the code.
- [ ] `artifacts/reports/pytest.xml`, coverage artifacts, and `artifacts/benchmarks/tts-vendor-latest.json` can be regenerated from documented commands.

## 9. Open Questions

1. Which Voice Library voices should be the defaults for `DEFAULT_PT_VOICE_ID` and `DEFAULT_EN_VOICE_ID`? To be picked when running task **3.6** (`scripts/voices_pt_br.py`) after Task 3 ships.
2. Should the Banking scenario include an English-speaking sub-flow (for foreign customers) to also exercise multilingual switching? Default: no, keep it PT-BR only and document multilingual as a follow-up.
3. Should the FastAPI WebSocket bridge be part of the scope or treated as a stretch goal? Current decision: stretch goal; descope first if time runs short.
4. Should the post-call webhook receiver be implemented? Current decision: **no** — use `client.conversations.list` / conversation retrieval from a small script (`scripts/conversations_list.py` or equivalent), document the [post-call webhooks](https://elevenlabs.io/docs/eleven-agents/workflows/post-call-webhooks) flow in [engineering/architecture/tech-stack-decisions.md](../../engineering/architecture/tech-stack-decisions.md), and link from `docs/walkthrough.md`.
5. What's the exact knowledge base shape for the Healthcare scenario? **Baseline locked**: five Markdown seed files under `data/kb/healthcare/` (~150–300 words each); RAG index computation uses Agents Platform KB APIs ([Knowledge base](https://elevenlabs.io/docs/eleven-agents/customization/knowledge-base), [Compute RAG index](https://elevenlabs.io/docs/eleven-agents/api-reference/knowledge-base/compute-rag-index)). Fine-grained chunk parameters follow whatever the SDK exposes at implementation time (confirm via `elevenlabs-docs` skill).
6. Which OpenAI TTS voice should be the default benchmark comparator? Baseline: `coral`, because it is commonly used in OpenAI examples and avoids tuning the comparison around voice preference. Revisit only after listening tests, not before the first latency run.
7. Should the repo also exercise the official [`elevenlabs/ui`](https://github.com/elevenlabs/ui) React registry? **Resolved**: yes, as an optional stretch (FR-23a, Task 6.7). Use `Orb`, `ConversationBar`, and `LiveWaveform` on a single Next.js page wired to `DEMO_AGENT_ID_TELECOM`. Optionally document discovery, deps, and friction in local-only notes at the repository root (see `.gitignore`) or in [`docs/reports/`](../../docs/reports/) (Task 7.9). A full React rewrite of the Python lab remains out of scope.
