# Quick guide: demo agents and `DEMO_AGENT_ID_*` variables

This note answers a common question: **you do not need to create the three agents manually in the ElevenLabs web UI** to use this repository. The recommended path is to **provision via the API** using this project’s code.

---

## What actually happens

| Layer | Behavior |
| --- | --- |
| **This repo** (`scripts/agent_create.py`) | Calls the ElevenLabs API to **create or update** the scenario agent (stable name in the directory) and **prints** the `agent_id` to the terminal. |
| **Your `.env` file** | Stores that `agent_id` in variables such as `DEMO_AGENT_ID_TELECOM` so scripts like `agent_simulate.py` and the Gradio UI know **which** agent to use **without hardcoding** it. |
| **ElevenLabs dashboard** | Optional to **confirm** the agent exists, inspect logs, and run tests — **not** the required creation step if you already ran `agent_create.py`. |

So “creating in the platform” already happens **via API** when you run local provisioning. You only **copy** the id the script prints into `.env`.

---

## `.env` prerequisites

At the repository root:

1. Copy `.env.example` to `.env` (if you have not already).
2. Fill in at least:
   - **`ELEVENLABS_API_KEY`** — from your account ([API keys](https://elevenlabs.io/app/settings/api-keys)).
   - **One agent voice id** (first match wins):
     - **`DEFAULT_AGENT_VOICE_ID`** — **recommended** for English demos: pick an English or multilingual voice from the Voice Library.
     - **`DEFAULT_EN_VOICE_ID`** — English Voice Library id used for Convai when `DEFAULT_AGENT_VOICE_ID` is unset (preferred over PT for English demos).
     - **`DEFAULT_PT_VOICE_ID`** — last fallback for agent provisioning; still drives the Gradio TTS playground, `apps/ws_bridge`, and the ElevenLabs leg of `tts_vendor_benchmark.py`.

Without `ELEVENLABS_API_KEY` and at least one of those voice ids, `agent_create.py` / `demo_prepare.py` fails while building the scenario.

### Defaults pushed by code (for your dashboard review)

When you provision from this repo, agents are configured with:

- **`language`:** `en` (Convai ASR/TTS locale — English conversation).
- **LLM:** `gemini-2.5-flash` (shared across telecom, banking, healthcare).
- **System prompt & first message:** English only (conversation and prompts aligned).

Stable agent names (upserted by name):

- `demo-telecom-sac-en`
- `demo-banking-sac-en`
- `demo-healthcare-triage-en`

After switching from older `-pt` agents, **re-run provisioning** and refresh **`DEMO_AGENT_ID_*`** in `.env` so Gradio and scripts target the new ids.

---

## Step-by-step (recommended flow)

Run from the repo root (`cd elevenlabs-agents-demo`).

### 1. Confirm the API responds

```bash
uv run python scripts/verify_api_keys.py
```

### 2. Provision each scenario and note the `agent_id`

**Shortcut (all three at once, writes `.env` for you):**

```bash
uv run python scripts/demo_prepare.py
```

**Or** run each scenario separately. Each command prints **one line**: that is the id to paste into `.env` if you are not using `demo_prepare.py`.

```bash
uv run python scripts/agent_create.py telecom
uv run python scripts/agent_create.py banking
uv run python scripts/agent_create.py healthcare
```

- **Telecom / Banking**: create/update the agent via `upsert` with prompts and tools from the matching module.
- **Healthcare**: additionally uploads files under `data/kb/healthcare/`, indexes RAG, then attaches documents to the agent — the first run may take longer.

### 3. Paste the ids into `.env`

Open `.env` and set (replace with the values **printed by the commands above**):

```env
DEMO_AGENT_ID_TELECOM=<paste_telecom_id_here>
DEMO_AGENT_ID_BANKING=<paste_banking_id_here>
DEMO_AGENT_ID_HEALTHCARE=<paste_healthcare_id_here>
```

Do not invent ids; use only the values from the terminal or dashboard for **that** agent.

### 4. Reload configuration

Scripts load settings when the process starts. If something was already running before you edited `.env`, open a new shell or restart so variables refresh.

### 5. Test simulation (optional but useful)

```bash
uv run python scripts/agent_simulate.py telecom "What is the balance on my line?"
```

Multi-turn script (each string is one simulated user turn, in order):

```bash
uv run python scripts/agent_simulate.py telecom --messages-file ./turns.json
```

Example `turns.json`:

```json
["Hello.", "I need to check my line.", "My tax id is 123.456.789-09."]
```

Requires the matching `DEMO_AGENT_ID_*` to be set. Output is a Rich panel with simulation summary, transcript, and tool calls.

---

## What if I only use the ElevenLabs website?

You **can** create an agent in the UI, copy `agent_id` from the panel, and paste it into `DEMO_AGENT_ID_*`. However:

- Prompts, tools, voice, and (for healthcare) the KB **will not** automatically match this repo’s scenarios.
- You would need to **manually replicate** the same configuration `telecom.py` / `banking.py` / `healthcare.py` already apply in code.

That is why the flow documented here is: **provision from the repo** → **paste ids into `.env`**.

---

## Where to see agents afterward

In the ElevenLabs app: **Conversational AI / Agents** (UI labels may change). You should see agents with stable names from code, for example:

- `demo-telecom-sac-en`
- `demo-banking-sac-en`
- `demo-healthcare-triage-en`

Running `agent_create.py` again **updates** the same agent (idempotent by name) instead of duplicating carelessly.

---

## Quick checklist

- [ ] `.env` has `ELEVENLABS_API_KEY` and at least one of `DEFAULT_AGENT_VOICE_ID` / `DEFAULT_PT_VOICE_ID` / `DEFAULT_EN_VOICE_ID`
- [ ] `DEFAULT_PT_VOICE_ID` is set if you use Gradio TTS playground, `apps/ws_bridge`, or the ElevenLabs vendor benchmark leg
- [ ] All three `agent_create.py` commands (or `demo_prepare.py`) completed successfully
- [ ] Three `DEMO_AGENT_ID_*` lines are filled with the printed ids
- [ ] `agent_simulate.py` tested for at least one scenario

---

*Local workflow aid; may be merged into `docs/walkthrough.md` or the README when docs are consolidated.*
