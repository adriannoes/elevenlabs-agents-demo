# End-to-End Walkthrough

This walkthrough takes a new reader from clone to the main demo paths in this repository: TTS, three ElevenAgents scenarios, RAG-backed healthcare triage, latency benchmarking, the Next.js reference surface, and the local WebSocket bridge.

The repo is a learning and product-engineering exploration of ElevenAgents and ElevenAPI. It is not a production application, compliance certification, or clinical / financial service. Scenario **domain** is Brazilian (CPF, LGPD, BRL); the three voice agents **speak English**.

## 1. Opening — What This Repo Explores

Start with the repository setup:

```bash
git clone https://github.com/adriannoes/elevenlabs-agents-demo.git
cd elevenlabs-agents-demo
cp .env.example .env
uv sync --extra dev --extra mcp
uv run python scripts/verify_api_keys.py
```

Fill `ELEVENLABS_API_KEY` in `.env`. For **agent provisioning**, set at least one of `DEFAULT_AGENT_VOICE_ID` (recommended for multilingual demos), `DEFAULT_EN_VOICE_ID`, or `DEFAULT_PT_VOICE_ID` (Convai prefers agent → EN → PT). To pick a Brazilian Portuguese voice for TTS and several scripts, run:

```bash
uv run python scripts/voices_pt_br.py
```

If the API check fails, fix credentials before trying live demos. If **no** agent voice variables are set, `demo_prepare.py` / `agent_create.py` cannot provision agents. Several surfaces (TTS playground, WebSocket bridge, vendor benchmark ElevenLabs leg) still require **`DEFAULT_PT_VOICE_ID`** specifically — set it even when you use `DEFAULT_AGENT_VOICE_ID` for agents if you want those tabs to work without extra wiring.

Useful entry points:

- [README](../README.md) — project overview and quick start.
- [Delivery record (tasks)](../engineering/tasks/tasks-prd-elevenlabs-vertical-exploration.md) — post-PRD summary and phase checklist.
- [Tech stack decisions](../engineering/architecture/tech-stack-decisions.md) — architecture and rejected alternatives.
- [Demo agent setup](../product/guides/demo-agent-setup.md) — `DEMO_AGENT_ID_*` and voice variables.
- **Fast prep:** `uv run python scripts/demo_prepare.py` verifies the key, provisions all three agents, and writes `DEMO_AGENT_ID_*` into `.env` (after `ELEVENLABS_API_KEY` and at least one agent voice id are set).

## 2. Telecom Demo

The Telecom path demonstrates a Brazilian-domain customer-care voice agent (English conversation) with identity check, server-tool lookup, and human escalation.

Provision the agent:

```bash
uv run python scripts/agent_create.py telecom
```

Copy the printed agent ID into `.env`:

```env
DEMO_AGENT_ID_TELECOM=<agent_id_from_terminal>
```

Optional simulation smoke test:

```bash
uv run python scripts/agent_simulate.py telecom "I want to check my line."
```

Multi-turn simulation (JSON file: array of user strings, one per turn):

```bash
uv run python scripts/agent_simulate.py telecom --messages-file path/to/turns.json
```

Example `turns.json`:

```json
["Hello.", "I want to check my line.", "My CPF is 123.456.789-09."]
```

Run the Gradio app and open the Telecom tab:

```bash
uv run python apps/gradio_app.py
```

Expected behavior: click **Start session**, allow microphone access, and speak in English. The agent should ask for CPF before account lookup and offer transfer for sensitive, off-topic, or human-requested cases.

Fallbacks:

- If the widget does not load, confirm `DEMO_AGENT_ID_TELECOM` and `ELEVENLABS_API_KEY`.
- If live audio fails due to browser or network permissions, use `agent_simulate.py` to test prompt and tool behavior.
- For the scenario narrative and risks, read [Telecom — Customer Care Demo](scenarios/telecom.md).

## 3. Banking Demo

The Banking path stresses high-trust interactions: authentication before tools, masked outputs, card actions, and Zero Retention Mode.

Provision the agent:

```bash
uv run python scripts/agent_create.py banking
```

Copy the printed agent ID into `.env`:

```env
DEMO_AGENT_ID_BANKING=<agent_id_from_terminal>
```

Optional simulation smoke test:

```bash
uv run python scripts/agent_simulate.py banking "I want to block my card."
```

Run the Gradio app and open the Banking tab:

```bash
uv run python apps/gradio_app.py
```

Expected behavior: the agent should request CPF and an approximate last transaction amount before any account-summary or card-action tool. Fraud, disputes, or ambiguous requests should route to `transfer_to_human`.

Fallbacks:

- If the agent refuses to use tools, verify the authentication details were provided in the simulated or spoken turn.
- If conversation history is unavailable, remember this scenario is provisioned with ZRM; use controlled tests and downstream systems for records.
- For compliance posture and PCI-DSS boundaries, read [Banking — Digital Banking Demo](scenarios/banking.md).

## 4. Healthcare + RAG

The Healthcare path is the only scenario that provisions knowledge-base documents and attaches them to the agent for RAG-backed triage language.

Provision the agent:

```bash
uv run python scripts/agent_create.py healthcare
```

Copy the printed agent ID into `.env`:

```env
DEMO_AGENT_ID_HEALTHCARE=<agent_id_from_terminal>
```

The first run may be slower because it uploads the six Markdown seeds under `data/kb/healthcare/` and requests RAG indexes. Later runs should reuse documents by name.

Optional simulation smoke test:

```bash
uv run python scripts/agent_simulate.py healthcare "I have had a high fever for two days and a cough."
```

Run the Gradio app and open the Healthcare tab:

```bash
uv run python apps/gradio_app.py
```

Expected behavior: the agent should avoid diagnosis, use source-backed language, suggest high-level routing, and escalate emergency symptoms such as severe chest pain, sudden neurological deficits, severe shortness of breath, or syncope. The tab also shows a source-documents panel so reviewers can see which KB documents were attached.

Fallbacks:

- If the source list is empty, run `agent_create.py healthcare` again and confirm provisioning completed.
- If RAG behavior looks generic, inspect `data/kb/healthcare/` and the agent configuration in the ElevenLabs dashboard.
- For the KB inventory, LGPD posture, and RAG flow, read [Healthcare — Triage Demo](scenarios/healthcare.md).

## 5. TTS Latency and Vendor Benchmark

The TTS path separates direct ElevenAPI exploration from agent demos.

Run a one-shot TTS demo:

```bash
uv run python scripts/tts_demo.py "Hello, this is a multilingual voice demo."
```

Run the ElevenLabs streaming TTFB benchmark:

```bash
uv run python scripts/tts_stream_ttfb.py --n 10 --model flash
```

Open the Gradio app for interactive controls:

```bash
uv run python apps/gradio_app.py
```

Use these tabs:

- **TTS Playground** — choose voice, model, output format, voice settings, and text normalization.
- **Latency** — runs repeated ElevenLabs streaming calls and plots TTFB.
- **Vendor Benchmark** — compares ElevenLabs and OpenAI TTS when `OPENAI_API_KEY` is present.

Run the vendor benchmark from the CLI:

```bash
uv run python scripts/tts_vendor_benchmark.py --n 3 --text-set short-pt-br
```

Expected behavior: the CLI prints a Rich summary table and writes `artifacts/benchmarks/tts-vendor-latest.json`.

Fallbacks:

- If `OPENAI_API_KEY` is missing, the vendor benchmark exits with setup guidance. The ElevenLabs latency tab and `tts_stream_ttfb.py` still work.
- If `DEFAULT_PT_VOICE_ID` is missing, run `scripts/voices_pt_br.py`, set the voice ID, and retry (needed for TTS playground, WebSocket bridge, and several benchmarks; agent provisioning can use `DEFAULT_AGENT_VOICE_ID` or `DEFAULT_EN_VOICE_ID` instead).
- The benchmark methodology lives in [`docs/benchmarks/tts-vendor-comparison.md`](benchmarks/tts-vendor-comparison.md). Treat CLI output as **local** evidence unless you align runs with that write-up.

Run the Voice Isolator CLI when you want to clean noisy audio before STT:

```bash
uv run python scripts/voice_isolator_demo.py data/samples/hello-pt-br.mp3 --out artifacts/clean.mp3
```

Expected behavior: the script writes a cleaned MP3, prints input/output byte counts and elapsed seconds, and suggests `uv run python scripts/stt_demo.py artifacts/clean.mp3` as the next step. This is a live ElevenLabs API call, so use a real API key and avoid committing generated audio artifacts.

## 6. Adoption Paths — Python Gradio vs React `elevenlabs/ui`

This repo intentionally has two UI paths.

### Python / Gradio: Primary Breadth Surface

Run:

```bash
uv run python apps/gradio_app.py
```

Use this when you want every demo in one local UI: TTS Playground, Telecom, Banking, Healthcare + RAG, Latency, and Vendor Benchmark.

### React / Next.js: Reference Surface

`apps/web/` is a minimal Next.js app using the official [`elevenlabs/ui`](https://github.com/elevenlabs/ui) registry (`Orb`, `ConversationBar`, `LiveWaveform`) plus `@elevenlabs/react`.

Set up from the repo root:

```bash
cd apps/web
cp .env.example .env.local
pnpm install
pnpm dev
```

Open <http://localhost:3000>.

The React app consumes the same `DEMO_AGENT_ID_TELECOM` provisioned by:

```bash
uv run python scripts/agent_create.py telecom
```

The trust boundary is different from Gradio: `apps/web/app/api/signed-url/route.ts` mints signed URLs server-side so `ELEVENLABS_API_KEY` never reaches the browser.

Decision framing:

- Choose **Gradio** for broad Python-first exploration and multi-vertical demos.
- Choose **React / Next.js** when a customer team wants to see the official registry and hook ergonomics.
- The stacks are isolated: `uv` / Python at the repo root, `pnpm` / Node under `apps/web/`.
- See [Tech Stack Decisions](../engineering/architecture/tech-stack-decisions.md) for the `elevenlabs/ui` evaluation and multi-stack rules.

## 7. Architecture and Next Steps

Architecture overview:

- `src/eleven_demo/client.py` centralizes ElevenLabs SDK access.
- `src/eleven_demo/config.py` centralizes environment loading and secret handling.
- `src/eleven_demo/scenarios/` defines vertical agent contracts.
- `src/eleven_demo/agents/` owns tools, KB helpers, provisioning, and simulation.
- `apps/gradio_app.py` is the primary demo UI.
- `apps/web/` is the React reference surface (signed URL).
- `apps/ws_bridge/` is a local-only FastAPI bridge for WebSocket TTS experiments.
- `scripts/mcp_telecom.py` is the lab MCP stdio server (telecom mock).
- `scripts/skills_model_drift.py` diffs `elevenlabs/skills` against Models docs.

Run the WebSocket bridge smoke path:

```bash
uv run uvicorn apps.ws_bridge.main:app --host 127.0.0.1 --port 8000
```

Then, in another terminal:

```bash
curl http://127.0.0.1:8000/healthz
```

Expected response:

```json
{"status":"ok"}
```

For binary TTS frames, connect a WebSocket client to `ws://localhost:8000/ws/tts` and send:

```json
{"text":"hello"}
```

Security warning: this bridge is unauthenticated and local-only. Do not expose it publicly without TLS, authentication, rate limiting, and logging redaction.

Post-call exploration without a webhook receiver:

```bash
uv run python scripts/conversations_list.py telecom --page-size 5
```

For a specific conversation:

```bash
uv run python scripts/conversations_list.py --id <conversation_id>
```

The CLI uses the Conversations API and redacts common CPF, email, phone, and card-number patterns before printing summaries. This is the local alternative to running a post-call webhook receiver in the demo repo. For a reference checklist on building a real webhook receiver (verification, PII, HTTPS), see [Post-call webhooks pattern](patterns/post-call-webhooks.md). Rationale for not hosting a receiver in this lab remains in [Tech Stack Decisions](../engineering/architecture/tech-stack-decisions.md).

Field notes and last-mile API contracts: [learning experience](../product/learning-experience.md), [pitfalls](pitfalls.md), [MCP lab server](mcp-lab-server.md), [upstream skills notes](upstream-skills-notes.md).

**Documentation backlog** (detail and checkboxes): [delivery record](../engineering/tasks/tasks-prd-elevenlabs-vertical-exploration.md). High-surface files: [`docs/benchmarks/tts-vendor-comparison.md`](benchmarks/tts-vendor-comparison.md), [`docs/reports/technical-exploration-report.md`](reports/technical-exploration-report.md), and generated evidence under `artifacts/` (see `scripts/generate_evidence_report.py`).

## Skills & Docs Alignment

This repo includes curated Cursor skills under `.cursor/skills/`:

- `elevenlabs-docs` — fetch live authoritative ElevenLabs docs.
- `elevenlabs-agents` — design, build, and operate ElevenAgents.
- `elevenlabs-api-cookbook` — production-shaped ElevenAPI snippets.
- `elevenlabs-visual-system` — local Gradio visual guidance.

These local skills are opinionated for this Python + Gradio stack. The upstream multi-language reference is the [`elevenlabs/skills`](https://github.com/elevenlabs/skills) bundle, which follows the [Agent Skills](https://agentskills.io/specification) front matter pattern. When details drift, prefer this source-of-truth order: official ElevenLabs docs, installed SDK signatures, upstream skills, then this repo's local cookbook.
