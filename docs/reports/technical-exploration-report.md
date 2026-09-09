# Technical Exploration Report

**Status**: evidence snapshot logged for Task **8.1** (2026-04-30); raw XML/JSON under `artifacts/` are gitignored — regenerate locally.
**Project**: ElevenLabs Vertical Exploration
**Last updated**: 2026-04-30
**Scope**: hands-on, single-developer Python lab. Not a production service, certification, or contractual benchmark.

---

## 1. Executive Summary

This report consolidates a hands-on exploration of [ElevenAgents](https://elevenlabs.io/docs/eleven-agents/overview) and [ElevenAPI](https://elevenlabs.io/docs/api-reference/introduction) targeted at Brazilian-market voice AI scenarios. The work covers six core threads:

- Three vertical voice agents (Telecom, Banking, Healthcare) provisioned idempotently from typed Python scenarios.
- Knowledge base + RAG end-to-end on the Healthcare scenario, with five PT-BR Markdown seeds and `get_or_create_rag_indexes`.
- Streaming TTS / batch + realtime STT / Voice Library / Voice Isolator wrappers around the official `elevenlabs` SDK.
- A local TTFB benchmark plus an optional cross-vendor comparison against OpenAI `gpt-4o-mini-tts`.
- Two demo surfaces sharing the **same** agent IDs: a primary Gradio multi-vertical playground and an optional Next.js reference app using the official [`elevenlabs/ui`](https://github.com/elevenlabs/ui) registry.
- Engineering discipline (typed config, retries, Pydantic v2 tool schemas, VCR-backed integration tests, ruff + pre-commit, redaction in CLI helpers).

Related deliverables:

- [PRD](../../product/prd/prd-elevenlabs-vertical-exploration.md)
- [Delivery record](../../engineering/tasks/tasks-prd-elevenlabs-vertical-exploration.md)
- [Tech stack decisions](../../engineering/architecture/tech-stack-decisions.md)
- [End-to-end walkthrough](../walkthrough.md)
- [TTS vendor benchmark methodology](../benchmarks/tts-vendor-comparison.md)

---

## 2. Background and Goals

The exploration started from a product question: *"Which ElevenLabs primitives are required to ship a credible PT-BR voice agent in regulated verticals, and where does the platform actually constrain product design?"*

Goals:

1. Exercise the full surface needed for an interactive voice product (TTS, STT, voices, agents, tools, knowledge base, RAG, conversation simulation, post-call inspection).
2. Generate **measured** evidence for the latency story — both intra-platform (Flash streaming) and cross-vendor (ElevenLabs vs OpenAI) — without overclaiming.
3. Demonstrate two adoption paths (Python / Gradio and React / Next.js) on the **same** provisioned agent, so the discussion of stack choice stays factual rather than ideological.
4. Keep all engineering artifacts reproducible: typed env loading, deterministic mocks for unit tests, VCR cassettes for integration tests, and committed scenario regression tests.

Non-goals (already documented in the [tech stack decisions](../../engineering/architecture/tech-stack-decisions.md)): real telephony, mobile, voice biometrics, multi-tenant deployment, and running Node tooling inside the Python pre-commit pipeline.

---

## 3. Architecture Overview

The runtime is intentionally small and Python-first. The Node surface under `apps/web/` is isolated by toolchain and only shares the `agent_id` and env-var names with the Python lab.

```text
src/eleven_demo/             Library: client factory, settings, TTS, STT, voices, agents,
                             metrics, scenarios, benchmarks
scripts/                     Thin CLI entry points (TTS, STT, voices, latency, benchmark,
                             provisioning, simulation, conversations list, voice isolator)
apps/gradio_app.py           Primary multi-vertical demo UI (six tabs)
apps/web/                    Optional Next.js reference using elevenlabs/ui (Task 6.7 shipped)
apps/ws_bridge/              Local-only FastAPI WebSocket TTS bridge (deep stretch)
tests/unit/                  Mocked unit tests
tests/integration/           VCR-backed integration tests + cassettes
docs/                        Walkthrough, scenarios, benchmark methodology, this report
data/kb/healthcare/          Five PT-BR Markdown seeds attached via RAG
.cursor/skills/              Local Cursor skills (docs, agents, api-cookbook, visual-system)
```

Key design choices (full rationale lives in [tech-stack-decisions.md](../../engineering/architecture/tech-stack-decisions.md)):

- **Single SDK entry point**: every module pulls the ElevenLabs SDK through `eleven_demo.client.get_client()`, which centralizes retry behavior on HTTP 429 / 5xx, timeouts, and auth.
- **Typed configuration**: `eleven_demo.config.Settings` (Pydantic v2 + `pydantic-settings`) loads `.env` and uses `SecretStr` for both `ELEVENLABS_API_KEY` and the optional `OPENAI_API_KEY` so secrets never leak into `repr` / logs.
- **Conversational AI namespace**: `get_client().conversational_ai.{agents, knowledge_base}` is the actual SDK path on the pinned version. The `agents` package wraps that namespace (`factory.upsert_agent`, `kb.upload_kb_text/file`, `compute_rag` via `get_or_create_rag_indexes`, `conversation_sim.simulate`).
- **Pydantic v2 for every external boundary**: env, scenario contracts, server-tool inputs/outputs, vendor benchmark report shape.
- **Async only where streaming requires it**: WebSocket TTS (`tts/ws.py`), realtime STT (`stt/realtime.py`), and the FastAPI bridge. Everything else stays sync for readability.
- **VCR cassettes** for integration tests so CI replays without burning credits, with `xi-api-key`, `authorization`, and vendor request IDs filtered.
- **Multi-stack isolation**: `apps/web/` ships its own `package.json`, `pnpm-lock.yaml`, and `node_modules/`. It does **not** appear in `pyproject.toml`, `uv.lock`, the Python pre-commit, or the Python coverage gates.

### Skills, spec alignment, and source-of-truth hierarchy

The repository's `.cursor/skills/` pack follows the [Agent Skills specification](https://agentskills.io/specification) (front matter with `name`, `description`, `license`, `compatibility`, optional `metadata.openclaw`) and is aligned with the upstream [`elevenlabs/skills`](https://github.com/elevenlabs/skills) bundle. The local cookbook is opinionated for this Python + Gradio stack (uses `get_client()`, the `Settings` defaults, VCR-backed tests), while the upstream bundle is the multi-language reference.

When details drift between sources, the exploration applied this **source-of-truth order**:

1. **Official ElevenLabs docs** (`elevenlabs.io/docs/llms.txt` + `/docs/...`).
2. **Installed SDK** (`inspect.signature(client.X.Y)` on the pinned version).
3. **Upstream `elevenlabs/skills`** (cross-language reference patterns).
4. **Local cookbook** under `.cursor/skills/elevenlabs-api-cookbook/SKILL.md`.

This ordering kept model IDs (`eleven_flash_v2_5`, `scribe_v2`, `scribe_v2_realtime`), endpoint names (`conversational_ai.knowledge_base.documents.create_from_*`, `get_or_create_rag_indexes`), and default behaviors honest against what the platform actually ships.

---

## 4. Demo Portfolio

| Demo | What it proves | Primary code | Storytelling |
|---|---|---|---|
| **TTS Playground** | Voice quality, model + format selection, voice settings, text normalization, request metadata, character-billing traceability via `with_raw_response`. | `eleven_demo.tts.sync`, `apps/gradio_app.py` | Walkthrough §5 |
| **Telecom Agent** | Server-tool account lookup, controlled human handoff, voice-friendly prompting, idempotent provisioning. | `eleven_demo.scenarios.telecom`, `agents/factory.upsert_agent` | [Telecom](../scenarios/telecom.md) |
| **Banking Agent** | Authentication-before-tool flow (CPF + last transaction amount), card actions, Zero Retention Mode posture. | `eleven_demo.scenarios.banking` | [Banking](../scenarios/banking.md) |
| **Healthcare Agent + RAG** | KB seed upload, RAG index computation, source-aware answers, ZRM for medical PII, source-document panel in Gradio. | `eleven_demo.scenarios.healthcare`, `data/kb/healthcare/*.md` | [Healthcare](../scenarios/healthcare.md) |
| **Latency Benchmark** | ElevenLabs Flash streaming TTFB across N runs, with median / p95 / mean. | `eleven_demo.tts.stream`, `eleven_demo.metrics.latency`, `scripts/tts_stream_ttfb.py` | Walkthrough §5 |
| **Vendor Benchmark** | Local, contextual ElevenLabs vs OpenAI TTS TTFB and total-time comparison on a fixed PT-BR utterance set, with randomized provider order per round. | `eleven_demo.benchmarks.tts_vendor`, `scripts/tts_vendor_benchmark.py` | [Methodology](../benchmarks/tts-vendor-comparison.md) |
| **Voice Isolator CLI** | Noisy-audio cleanup before STT, real ElevenAPI call surfaced in a one-shot script. | `scripts/voice_isolator_demo.py` | Walkthrough §5 |
| **Post-call inspection** | Local alternative to running an HTTP webhook receiver; redacts CPF, email, phone, and card patterns before printing summaries. | `scripts/conversations_list.py` | [ADR — webhooks](../../engineering/architecture/tech-stack-decisions.md) |

Each agent scenario is provisioned with `scripts/agent_create.py <scenario>` and exercised either via the simulate CLI (`scripts/agent_simulate.py`) or the Gradio widget (signed URL, no API key in the browser).

### 4.1 Reference React surface using `elevenlabs/ui`

Task 6.7 shipped under [`apps/web/`](../../apps/web/README.md): a minimal Next.js 14 (App Router, TypeScript, Tailwind) page using the official [`elevenlabs/ui`](https://github.com/elevenlabs/ui) registry.

- **Components consumed**: `Orb`, `ConversationBar`, `LiveWaveform` (added via `pnpm dlx shadcn@latest add ...`), composed in `components/telecom-agent-console.tsx`.
- **Conversation hook**: `useConversation` from `@elevenlabs/react`, mapping the agent state machine (`disconnected → connecting → connected → disconnecting`) to the orb's `idle / thinking / talking / listening` semantics.
- **Trust boundary**: `app/api/signed-url/route.ts` calls `client.conversations.get_signed_url(agent_id=...)` server-side using `ELEVENLABS_API_KEY` from `process.env` and returns only `{ signedUrl }`. The raw key is never exposed via `NEXT_PUBLIC_*` env vars or visible in the client bundle.
- **Interoperability**: the React app and the Gradio Telecom tab consume the **same** `DEMO_AGENT_ID_TELECOM` provisioned by `scripts/agent_create.py telecom`. There is no Python-to-Node code sharing — only env-var names.
- **Toolchain isolation**: Node 20+ / pnpm under `apps/web/`; build / lint of this surface is verified manually and does **not** block the Python release run.

Observed friction worth recording for anyone maintaining `apps/web/`:

- `pnpm` next to `uv` adds two parallel lockfiles and CI surfaces; the project keeps them strictly separate by directory.
- The signed-URL route is the single trust boundary — easy to get wrong if `ELEVENLABS_API_KEY` is renamed to a `NEXT_PUBLIC_*` variant by mistake.
- Bundle size grows quickly with `three` + `@react-three/fiber` + `@react-three/drei` (Orb dependencies); acceptable for a single conversation page, but worth flagging before adopting more registry components.

If a future iteration drops Task 6.7, replace this sub-section with a one-paragraph pointer to the `elevenlabs/ui` evaluation block in [tech-stack-decisions.md](../../engineering/architecture/tech-stack-decisions.md).

---

## 5. Benchmark Results

Benchmark numbers are intentionally **contextual**: they depend on local network conditions, provider routing, model load, voice choice, output format, and account tier. Treat them as decision-quality intuition, not as universal vendor verdicts.

### 5.1 ElevenLabs streaming TTFB (intra-platform)

`scripts/tts_stream_ttfb.py --n 10 --model flash` runs N streaming TTS calls through `eleven_demo.tts.stream.stream()` and aggregates TTFB through `eleven_demo.metrics.latency.LatencyReport` (median, p95, mean, min, max, count). The Gradio **Latency** tab uses the same primitives and renders a line chart + raw sample table.

Expected ranges (Flash v2.5, `mp3_22050_32`, PT-BR voice, residential connection): tens to a few hundred milliseconds for TTFB, with p95 sensitive to network jitter. Re-run from the target deployment region rather than copying numbers across machines.

### 5.2 Cross-vendor smoke (ElevenLabs vs OpenAI)

The vendor benchmark CLI exists at `scripts/tts_vendor_benchmark.py`. A **single-shot smoke artifact** is committed under [`artifacts/benchmarks/tts-vendor-smoke.json`](../../artifacts/benchmarks/tts-vendor-smoke.json) to demonstrate the report shape; it is **not** a representative comparison. The shape matches `VendorBenchmarkReport.model_dump()` (per-run `provider`, `model_id`, `voice`, `output_format`, `text_id`, `ttfb_ms`, `total_ms`, `byte_count`; aggregated `summaries`; `hypothesis`; `caveats`).

Smoke snapshot (n=1 per provider, single PT-BR phrase, single laptop, single network — illustrative only):

| Provider | Model | Voice | Format | TTFB (ms) | Total (ms) | Bytes |
|---|---|---|---|---:|---:|---:|
| ElevenLabs | `eleven_flash_v2_5` | `JBFqnCBsd6RMkjVDRZzb` | `mp3_22050_32` | 527.8 | 630.6 | 14,569 |
| OpenAI | `gpt-4o-mini-tts` | `coral` | `mp3` | 2,148.9 | 2,563.0 | 75,264 |

**Task 8.1 regeneration (2026-04-30):** the vendor CLI did not write `artifacts/benchmarks/tts-vendor-latest.json` because `DEFAULT_PT_VOICE_ID` was unset in the automation environment (expected setup hint, exit code 2). With both `DEFAULT_PT_VOICE_ID` and `OPENAI_API_KEY` set, rerun per §5.3.

Read this as: in a one-shot smoke on the captured machine and network, ElevenLabs Flash v2.5 reached the first audio chunk noticeably sooner. **Do not** generalize from a single sample — rerun with `--n 5` or higher and capture the environment fields documented in the [methodology](../benchmarks/tts-vendor-comparison.md#environment-fields-to-record-with-each-published-run).

### 5.3 How to reproduce

```bash
uv run python scripts/tts_stream_ttfb.py --n 10 --model flash
uv run python scripts/tts_vendor_benchmark.py --n 5 --text-set short-pt-br \
    --out artifacts/benchmarks/tts-vendor-latest.json
```

Without `OPENAI_API_KEY` or `DEFAULT_PT_VOICE_ID`, the vendor CLI exits with a setup hint and **no stack trace** (codes `2` / validation); the ElevenLabs streaming path keeps working independently when only the OpenAI leg is missing.

---

## 6. Testing Evidence

The test pyramid mirrors the library layout. Unit tests live under `tests/unit/` with mocked SDK calls; integration tests live under `tests/integration/` and are gated by `@pytest.mark.integration` plus VCR cassettes recorded once per scenario.

Coverage of the test surface as committed:

- **Unit modules**: 32 files spanning client retry, settings, TTS sync/stream/ws, STT batch + realtime, voices catalog, latency metrics, agents factory/tools/kb/simulate, scenario base + per-vertical configs, vendor benchmark, voice isolator CLI, conversations CLI, and the WebSocket bridge.
- **Integration modules**: 6 files (TTS sync, TTS stream, STT batch, three scenario regression tests for telecom / banking / healthcare). The vendor benchmark integration is opt-in and skipped when either API key is missing and no cassette exists.

To regenerate machine-readable evidence (per Task 8.1):

```bash
uv run pytest -n auto --junitxml=artifacts/reports/pytest.xml -m "not integration"
uv run pytest --cov=src/eleven_demo \
    --cov-report=term \
    --cov-report=xml:artifacts/reports/coverage.xml \
    --cov-report=html:artifacts/reports/htmlcov \
    --cov-fail-under=80 -m "not integration"
uv run pytest -m integration --junitxml=artifacts/reports/integration-pytest.xml
uv run pre-commit run --all-files 2>&1 | tee artifacts/reports/pre-commit.txt
uv run python scripts/tts_vendor_benchmark.py --n 5 --text-set short-pt-br \
    --out artifacts/benchmarks/tts-vendor-latest.json
uv run python scripts/generate_evidence_report.py
```

Expected artifact paths after the release run:

- `artifacts/reports/pytest.xml`
- `artifacts/reports/integration-pytest.xml`
- `artifacts/reports/coverage.xml`
- `artifacts/reports/htmlcov/`
- `artifacts/reports/pre-commit.txt`
- `artifacts/benchmarks/tts-vendor-latest.json`

### Evidence snapshot (local regeneration, 2026-04-30)

Snapshot at the time of the report (unit count has since grown).

| Gate | Result |
| --- | --- |
| Unit tests (`-m "not integration"`, xdist) | 118 passed (JUnit: `artifacts/reports/pytest.xml`) |
| Integration replay | 7 collected, **3 passed**, **4 skipped** — at snapshot time, some legs still needed `DEFAULT_PT_VOICE_ID` or live keys when cassettes were missing |
| Coverage on `src/eleven_demo/` | **95.03%** lines (cobertura); **87.75%** branches; PRD gate ≥80% satisfied |
| Ruff | `check` + `format --check` clean |
| Pre-commit | all hooks passed (log: `artifacts/reports/pre-commit.txt`) |
| Optional `apps/web` | `pnpm install --frozen-lockfile` + `pnpm build` **passed** (Next.js 14.2.35; build reported ~476 kB First Load JS for `/`) |
| Vendor JSON | `tts-vendor-latest.json` **not** produced without `DEFAULT_PT_VOICE_ID`; committed smoke shape remains at [`artifacts/benchmarks/tts-vendor-smoke.json`](../../artifacts/benchmarks/tts-vendor-smoke.json) |

Machine-readable paths under `artifacts/` are **gitignored**; this table is the portable record committed with the repo. Re-run the block above (with a filled `.env`) to refresh numbers, then `uv run python scripts/generate_evidence_report.py` for a Markdown digest.

Coverage gate: PRD FR-24 targets ≥80% on `src/eleven_demo/`. Line rates come from `coverage.xml` (lines-valid / lines-covered); pytest prints a combined percentage that weights branches — both are logged in the CI-style invocation above.

Known skips:

- Integration tests skip cleanly when neither `ELEVENLABS_API_KEY` nor a VCR cassette is available (`tests/conftest.py`).
- The vendor benchmark integration test is double-gated (both API keys or a cassette). Cassettes filter `xi-api-key`, `authorization`, and OpenAI request IDs.
- Scenario `simulate` tests do **not** skip on `DEFAULT_PT_VOICE_ID`; they skip when neither a cassette nor a live `ELEVENLABS_API_KEY` + `DEMO_AGENT_ID_*` is available (`tests/integration/scenarios/_support.py`). The vendor benchmark integration leg still needs `DEFAULT_PT_VOICE_ID` when recording.

---

## 7. Product Insights

These are working hypotheses validated during implementation, not platform-wide claims:

- **Streaming TTS is the right default for conversational UX**, not full-file synthesis. The TTFB story and the vendor smoke both reinforce this.
- **Flash-class models** are the right baseline for turn-by-turn voice agents; Multilingual / v3 are reserved for higher-quality, less interactive moments (one-shot TTS Playground, Healthcare KB read-backs).
- **Privacy posture is a product feature, not an add-on**. Banking and Healthcare scenarios enable Zero Retention Mode at provisioning time and document the trade-off (no replay of conversations through `conversations.get` once ZRM is on).
- **Tool calling + KB grounding** make voice agents easier to trust *and* easier to operate. The Healthcare scenario shows the difference: a non-RAG version drifts into clinical advice; the RAG-backed version routes confidently to specialties and documented escalation criteria.
- **Idempotent provisioning** is non-negotiable. `agents.factory.upsert_agent` (find by name, then create or update) keeps the workspace clean across reruns and lets `scripts/agent_create.py <scenario>` be safe to run repeatedly.
- **Two adoption paths reduce stack debate**. Showing the same agent from Gradio (Python team) and from `elevenlabs/ui` (React team) makes the conversation about which surface fits the product, not about which framework is "right".
- **Benchmarks need methodology before numbers**. The vendor comparison ships with a methodology doc, randomized provider ordering, and JSON output that is honest even when results do not favor a preferred vendor.

---

## 8. Risks and Limitations

- **Local laboratory, not a production system**. The Gradio app, the FastAPI bridge, and `apps/web/` are local-only. No TLS, no authentication, no rate limiting, no tenant isolation.
- **Synthetic data only**. Server-tool mocks (`agents/tools.py`) generate deterministic-but-fake account, card, and appointment data. Healthcare KB seeds are fictional and explicitly non-clinical.
- **Benchmark variance**. TTFB measurements vary by region, time of day, network type, account tier, and model load. A single-shot smoke artifact is not a representative comparison.
- **Language scope**. PT-BR utterance set, PT-BR voice defaults, PT-BR scenario prompts. Cross-language behavior is not exercised.
- **Cassette drift**. SDK upgrades may invalidate cassettes; the recorded scenario / TTS / STT cassettes must be re-recorded if `elevenlabs` or `openai` packages move.
- **Webhook flow not implemented**. Post-call analysis uses `conversations.list` / `get` via `scripts/conversations_list.py` rather than a long-lived HTTP receiver. Production flows that need durable, signed records should build a dedicated authenticated receiver instead of extending this lab.
- **Multi-stack discipline matters**. `apps/web/` is intentionally outside Python tooling; failing to keep that boundary will mix `pnpm` and `uv` failure modes in CI.

---

## 9. Next Steps

Short list, in priority order:

1. **Re-run Task 8.1 locally** with a complete `.env` (`DEFAULT_PT_VOICE_ID`, both API keys as needed) so `artifacts/benchmarks/tts-vendor-latest.json` and all integration tests fill in, then refresh §6 **Evidence snapshot** if numbers change materially.
2. **Vendor benchmark at `--n ≥ 5`** from the target deployment region and paste JSON + environment block into [`docs/benchmarks/tts-vendor-comparison.md`](../benchmarks/tts-vendor-comparison.md).
3. **Capture scenario regression conversation IDs** in `tests/integration/scenarios/` after the next replay, so prompt drift is observable through stable tool-call signals rather than verbatim wording.
4. **Re-evaluate model defaults** when ElevenLabs ships a new Flash / Scribe revision — using the source-of-truth hierarchy (docs → SDK → upstream skills → local cookbook) to avoid silent drift.

A reader who finishes this report should be able to (a) summarize what was built and why, (b) point to the evidence that supports each claim, and (c) know exactly which commands to run to regenerate that evidence.
