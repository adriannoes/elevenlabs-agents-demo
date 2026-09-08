# Pitfalls from live smoke tests

Short troubleshooting page for the four integration details that mocks did not catch. Full narrative: [Learning experience](../product/learning-experience.md). None of these are platform outages — they are contracts you want in the first cookbook example.

## 1. Webhook tool `request_body_schema` is not full JSON Schema

**Symptom:** Agent provisioning or tool update returns a validation error on `request_body_schema`. A direct `model_json_schema()` dump from Pydantic looks right locally and fails on the API.

**What the API wanted in this lab:** an object with `type`, `required`, and `properties` whose values are literal `boolean` / `string` / `integer` / `number` (optional `enum`, `description`). No `title`, no `additionalProperties`, no `anyOf` for optional/nullable fields.

**What we do:** `_to_elevenlabs_tool_body_schema` in `src/eleven_demo/scenarios/base.py` strips the dump down to that subset.

**Try:** `uv run python scripts/agent_create.py telecom` and inspect the stored tool schema in the dashboard if the call fails.

## 2. `simulate_conversation` first turn is `[]`, not `None`

**Symptom:** Simulation raises on `partial_conversation_history=None`. Or the simulated "user" answers like an assistant ("As an AI language model…").

**What worked:** pass an empty list for the first turn; set an explicit simulated-user prompt (this lab uses a Brazilian customer persona in `SIMULATED_USER_PROMPT` even when the agent speaks English). Budget ~120s HTTP timeout for multi-turn runs with tools.

**Code:** `src/eleven_demo/agents/conversation_sim.py`. CLI: `uv run python scripts/agent_simulate.py telecom "I want to check my line."`

## 3. Voice Isolator rejects too-short audio

**Symptom:** First isolator call fails with a clear API error about minimum duration. A tiny generated fixture is not enough.

**What we do:** `scripts/voice_isolator_demo.py` sends a real file (`data/samples/hello-pt-br.mp3`). If you generate a smoke WAV, make it longer than a fraction of a second.

**Try:**

```bash
uv run python scripts/voice_isolator_demo.py data/samples/hello-pt-br.mp3 --out artifacts/clean.mp3
```

## 4. Voice Library locale labels are not a reliable PT-BR filter

**Symptom:** `scripts/voices_pt_br.py` returns 200 and zero voices tagged the way you expected.

**What we do:** print a small sample and ask you to set `DEFAULT_PT_VOICE_ID` (and `DEFAULT_EN_VOICE_ID` / `DEFAULT_AGENT_VOICE_ID` for Convai). Do not block the demo on metadata.

**Try:** `uv run python scripts/voices_pt_br.py` then paste an id into `.env`.

## Related

- [Walkthrough](walkthrough.md)
- [MCP lab server](mcp-lab-server.md)
- [Upstream skills notes](upstream-skills-notes.md)
