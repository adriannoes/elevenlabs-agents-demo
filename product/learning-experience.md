> A first-person memo from a developer who built a real integration against the ElevenLabs platform using only public surfaces — docs, the installed SDKs, and the official `elevenlabs/skills` bundle. Written as a field note, not a bug report. Some of this friction is the same friction a customer integration team hits when they leave the quickstart.

**Repo**: <https://github.com/adriannoes/elevenlabs-agents-demo>

**Verified**: 2026-05-05 (original pass) · **re-verified**: 2026-09-08 against live docs and `elevenlabs/skills` `main`.

---

## Why this exists

I wanted hands-on intuition for how **ElevenAgents** and **ElevenAPI** fit together when you have to ship something realistic: voice agents, tools, knowledge base, a browser surface that never sees the API key, and a TTS latency check. The repository above is that lab.

I constrained myself to the public surfaces a new developer actually gets: the [official documentation](https://elevenlabs.io/docs), the pinned `elevenlabs` Python SDK, `@elevenlabs/elevenlabs-js` / `@elevenlabs/react` on the Node side, and the [`elevenlabs/skills`](https://github.com/elevenlabs/skills) GitHub bundle. No internal channels. The point was to feel the developer journey, not to skip it.

If a single developer notices a mismatch between two ElevenLabs-owned pages, customer teams will too, and they will notice it at scale.

---

## How I navigated the platform

I started with the docs alone. Mid-way through, I found the skills bundle because the [ElevenAPI quickstart](https://elevenlabs.io/docs/eleven-api/quickstart) still opens with:

> "Use the [ElevenLabs text-to-speech skill](https://github.com/elevenlabs/skills/tree/main/text-to-speech) to generate speech from your AI coding assistant: `npx skills add elevenlabs/skills --skill text-to-speech`"

That is a deliberate Day-0 signal. The docs promote the bundle as the onboarding path for anyone working inside an AI coding assistant. So I treated it as part of the documentation experience: read the skills, compare them to the Models page, and keep a local cookbook that is allowed to be wrong until re-checked.

Trust order I still use:

1. **Official docs** (`elevenlabs.io/docs`, via `llms.txt` then the specific page). Canonical for model IDs, deprecation, and request shapes.
2. **Installed SDK** — `inspect.signature(client.X.Y)` on the version pinned in `pyproject.toml`. What code can actually run today.
3. **`elevenlabs/skills`** — first artifact many AI-assisted developers will load. Should inherit from (1).
4. **Local cookbooks** — convenience; assumed to drift; re-verified against (1) and (2).

That lookup protocol lives in [`.cursor/skills/elevenlabs-docs/SKILL.md`](https://github.com/adriannoes/elevenlabs-agents-demo/blob/main/.cursor/skills/elevenlabs-docs/SKILL.md).

---

## What I noticed, still true on 2026-09-08

Each row below was re-fetched on 2026-09-08. These are not regressions I invented in May; they are still visible on the live surfaces.

### 1. Turbo models — two ElevenLabs surfaces still disagree

The upstream skill [`text-to-speech/SKILL.md`](https://github.com/elevenlabs/skills/blob/main/text-to-speech/SKILL.md) still lists `eleven_turbo_v2_5` and `eleven_turbo_v2` in its Models table next to Flash, with no deprecation note.

The canonical [Models page](https://elevenlabs.io/docs/overview/models) still lists those IDs under **Deprecated models** and says to use Flash instead:

> "The `eleven_turbo_v2_5` and `eleven_turbo_v2` models are functionally equivalent to the `eleven_flash_v2_5` and `eleven_flash_v2` models respectively, except the latency on the Flash models is lower on average. We recommend using the Flash models over Turbo models in all use cases."

A developer who follows the quickstart's `npx skills add` instruction lands on the skill table first. Nothing in the SDK rejects Turbo; requests succeed.

This lab ships a check you can re-run:

```bash
uv run python scripts/skills_model_drift.py
```

It compares the skill markdown to `/docs/overview/models.md` and exits 1 when a Turbo row in the skill table lacks a deprecation note. Methodology and a patch sketch: [`docs/upstream-skills-notes.md`](../docs/upstream-skills-notes.md).

### 2. STT keyterm cap still differs by 10×

[Models](https://elevenlabs.io/docs/overview/models) still advertises *"Keyterm prompting, up to 1000 terms"* for Scribe v2. The upstream [`speech-to-text/SKILL.md`](https://github.com/elevenlabs/skills/blob/main/speech-to-text/SKILL.md) still says *"up to 100 terms"*. Same feature, same vendor, two numbers. The skill IDs themselves (`scribe_v2`, `scribe_v2_realtime`) are aligned — that part is in good shape.

`scribe_v1` remains listed as outclassed and still works at runtime. A cookbook that copied v1 will not get a hard failure.

### 3. The skills bundle is still on the critical path

The ElevenAPI quickstart (re-checked 2026-09-08) still opens with `npx skills add elevenlabs/skills --skill text-to-speech`. The Voice Isolator cookbook still does the same pattern. Drift in a single skill is felt on Day 0.

The quickstart also documents `elevenlabs generate-skills`, which writes a `SKILL.md` per CLI command group from the installed CLI's own API definition. That is a strong mechanism: the generated skills cannot lag the CLI version you have. The *hand-written* bundle on GitHub does not have an equivalent check against `/docs/overview/models`.

### 4. Three `elevenlabs*` JS packages, one warning, still easy to miss

Unchanged in spirit on 2026-09-08:

- `elevenlabs` on npm — outdated v1.x. The [skills README](https://github.com/elevenlabs/skills/blob/main/README.md) still warns: *Always use `@elevenlabs/elevenlabs-js`. Do not use `npm install elevenlabs`.*
- `@elevenlabs/elevenlabs-js` — ElevenAPI (TTS, STT, isolation, signed URLs in this repo's Route Handler).
- `@elevenlabs/client` / `@elevenlabs/react` — ElevenAgents conversation in the browser.

The deprecation warning still lives primarily in the skills README. Each docs area uses the correct package for its surface. A developer who searches npm for "elevenlabs" still has to triangulate.

This lab's Next.js app uses `@elevenlabs/elevenlabs-js` server-side and `@elevenlabs/react` in the browser, with the key only on the server. See [`apps/web/README.md`](../apps/web/README.md).

---

## What changed since the May notes

Worth recording so this memo does not pretend the platform stood still:

- **Hosted MCP** (announced mid-August 2026): `https://api.elevenlabs.io/v1/mcp`, OAuth, nothing to install. Docs: [Hosted MCP server](https://elevenlabs.io/docs/eleven-agents/operate/hosted-mcp). Blog: [ElevenLabs Hosted MCP in Claude](https://elevenlabs.io/blog/elevenlabs-mcp-in-claude).
- **Local `elevenlabs/elevenlabs-mcp`** was [archived 2026-08-20](https://github.com/elevenlabs/elevenlabs-mcp) in favor of the hosted server. A GitHub search for "ElevenLabs MCP" still surfaces the archived repo first for some queries. That is a classic developer-journey fork: the README is honest once you open it; discovery is not.
- **Agents can also consume external MCP servers** as tools ([MCP tools](https://elevenlabs.io/docs/eleven-agents/customization/tools/mcp)) — a different direction from "manage my workspace from Claude."
- **Models page** now leads with `eleven_v3` and `eleven_v3_conversational` alongside Flash. The quickstart example uses `eleven_v3`. Interactive agents in this lab still default to Flash for turn-taking latency; that remains a product choice, not a docs bug.
- **CLI `generate-skills`** is now documented on the quickstart as the way to keep assistant skills in lockstep with the installed CLI.

---

## What only live smoke tests surfaced (API contracts)

Unit tests had the right shape. The live API taught the request contracts.

**Webhook tool schema.** Agents rejected a raw Pydantic JSON Schema dump. The accepted subset is literal properties with descriptions, no `title`, no `additionalProperties`, no `anyOf` for nullables. The lab encodes that in `_to_elevenlabs_tool_body_schema` in `src/eleven_demo/scenarios/base.py`. A Python example of the *accepted* schema in the public docs would save teams a round-trip.

**`simulate_conversation`.** `partial_conversation_history=None` failed; an empty list is the first-turn shape. The default simulated user did not sound like a customer until we passed an explicit persona prompt. Timeouts for multi-turn runs needed to be on the order of two minutes, not a generic HTTP 30s. See `src/eleven_demo/agents/conversation_sim.py`.

**Voice Isolator.** The first live call failed because the generated fixture was below the minimum duration. The error was clear. The cookbook would be stronger if it stated the minimum up front. CLI: `scripts/voice_isolator_demo.py`.

**Voice Library locale labels.** A naive PT-BR filter returned no rows even though the call succeeded. The lab falls back to a sample plus "set `DEFAULT_PT_VOICE_ID` yourself." If locale search is a supported path, stable labels would help.

These four are expanded as a troubleshooting page: [`docs/pitfalls.md`](../docs/pitfalls.md).

None of them were blockers. They are the last mile an integration engineer hits with a customer team. Docs are strong on navigation; production-shaped examples win when they include the runtime contract.

---

## MCP as a developer surface

There are now three MCP stories a new developer can land on, and they are easy to conflate:

| Surface | Role | What this lab does |
| --- | --- | --- |
| **Hosted MCP** `https://api.elevenlabs.io/v1/mcp` | Manage agents from Claude / Cursor (OAuth, no local process) | Documented, not reimplemented — it is a platform product |
| **Archived local MCP** `elevenlabs/elevenlabs-mcp` | Historical stdio server with an API key | Not vendored; README points at the archive notice |
| **Agents → external MCP tools** | An ElevenLabs agent calls *your* MCP server | Not covered here; the lab server is stdio-only (an agent-attached MCP needs an HTTP transport and a reachable URL) |
| **This repo's stdio server** | One mock tool, same contract as the webhook | `uv run python scripts/mcp_telecom.py` |

The lab server exposes `lookup_telecom_account` — the same deterministic mock the Telecom agent webhook uses — over MCP stdio. It exists so you can feel "I attached a tool server" without standing up OAuth or a public tunnel. It is explicitly **not** an official ElevenLabs MCP.

```bash
uv run python scripts/mcp_telecom.py
```

Point an MCP client at that command. Implementation: `src/eleven_demo/mcp/server.py`. Notes: [`docs/mcp-lab-server.md`](../docs/mcp-lab-server.md).

---

## `elevenlabs/ui` in one paragraph

After the Gradio skeleton worked, I added a second adoption path: the same Telecom agent on a Next.js page using the official [`elevenlabs/ui`](https://github.com/elevenlabs/ui) registry (`Orb`, `ConversationBar`, `LiveWaveform`) and `@elevenlabs/react`. Signed URLs are minted in `app/api/signed-url/route.ts` with `@elevenlabs/elevenlabs-js`. Python stays the breadth surface (provisioning, tests, TTS/STT). The Node app is one conversation page. Friction worth knowing: two lockfiles, two env files, and a heavy `three` bundle for Orb. Details stay in [tech-stack-decisions.md](../engineering/architecture/tech-stack-decisions.md).

---

## Things that still work beautifully

- [`/docs/llms.txt`](https://elevenlabs.io/docs/llms.txt) — index-first navigation for agents and humans.
- [Models](https://elevenlabs.io/docs/overview/models) — deprecation table with replacements. The missing piece is making every other surface obey it.
- Agents docs still separate configure / deploy / monitor in a way that matches how teams split work.
- Python SDK `client.conversational_ai.*` still matches the docs when you `inspect.signature`.
- Hosted MCP + OAuth is the right default for "talk to my workspace from Claude." Archiving the local server with a banner is honest — discovery of that banner could be more prominent.

---

## What I would ship (small, mechanical)

Offered as a developer who would be glad to be wrong about scope:

1. **Mark Turbo deprecated in `elevenlabs/skills` `text-to-speech/SKILL.md`** — same table, add a deprecation line and point at Flash. The Models page already has the copy. Patch sketch: [`docs/upstream-skills-notes.md`](../docs/upstream-skills-notes.md).
2. **Align the Scribe keyterm cap** in `speech-to-text/SKILL.md` with Models (1000), or footnote the skill if 100 is a different product limit.
3. **A drift-check Action on `elevenlabs/skills`** that diffs model tables against `/docs/overview/models.md` weekly. This repo's `scripts/skills_model_drift.py` is a working prototype of that diff (Turbo + keyterm cap). Happy to adapt it upstream.
4. **A one-screen "which JS package?" map** on the docs landing / ElevenAPI quickstart — the warning the skills README already carries, plus the Agents client, plus a line that `npm install elevenlabs` is the wrong package.
5. **A "hosted MCP vs archived local vs agent-attached MCP"** paragraph near both MCP docs, so GitHub search for the archived repo does not become the Day-0 path.

None of this is a new product. It is keeping the surfaces the docs already tell developers to trust in lockstep.

---

## About this repository

<https://github.com/adriannoes/elevenlabs-agents-demo>

Python lab, Next.js reference page, tests, and the notes above. Highlights:

- **`src/eleven_demo/client.py`** — single `get_client()` factory, retries on 429/5xx.
- **`src/eleven_demo/scenarios/`** — Telecom / Banking / Healthcare contracts, webhook schema subset, Healthcare KB + RAG.
- **`src/eleven_demo/mcp/`** — stdio MCP server for the telecom mock tool.
- **`scripts/skills_model_drift.py`** — live diff of skills vs Models.
- **`apps/web/`** — signed URL + `@elevenlabs/react`.
- **`docs/pitfalls.md`** — the four live-smoke failures as a troubleshooting page.
- **Tests** — unit tests plus VCR integration replayed locally; CI runs unit tests only.

The goal of the repo is learning. The goal of this memo is to make some of that learning useful to people who maintain the developer journey.
