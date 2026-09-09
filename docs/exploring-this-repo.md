# Exploring this repository

This is a **hands-on learning lab** for [ElevenAgents](https://elevenlabs.io/docs/eleven-agents/overview) and [ElevenAPI](https://elevenlabs.io/docs/api-reference/introduction). It is not a production service or a compliance benchmark. It covers SDK usage (Python and JS), signed URLs, a small MCP tool server, Brazilian-market **voice scenarios** (telecom, banking, healthcare), and latency measurement. Agent conversations are English; the domain (CPF, LGPD, BRL) stays Brazilian.

Start with the [learning experience memo](../product/learning-experience.md) if you want the developer-journey notes first, then the [end-to-end walkthrough](walkthrough.md).

## Quick commands

After [Quick start](../README.md#quick-start) (clone, `uv sync --extra dev --extra mcp`, `.env` with `ELEVENLABS_API_KEY` and voice/agent variables as needed):

```bash
uv run python scripts/demo_prepare.py
```

```bash
uv run python apps/gradio_app.py
```

The first command verifies the API key and provisions or updates the three demo agents; the second opens the Gradio playground.

## Where to read next

- [Learning experience](../product/learning-experience.md) — field notes from public docs, skills, and the live API.
- [Pitfalls](pitfalls.md) — webhook schema, simulate, isolator, Voice Library locale.
- [MCP lab server](mcp-lab-server.md) — stdio tool server (not hosted MCP).
- [Walkthrough](walkthrough.md) — full path through surfaces and scripts.
- [Technical exploration report](reports/technical-exploration-report.md) — architecture and evidence snapshot.

## Design choices in this lab

- **Single SDK entry** — All ElevenLabs access goes through `eleven_demo.client.get_client()` (retries on 429/5xx, no ad-hoc client constructors).
- **Integration tests** — HTTP traffic is replayed locally with VCR cassettes where possible. CI runs unit tests plus cassette replay with a placeholder key and does not consume credits.
- **Browser and Next.js** — `apps/web` mints **signed URLs** server-side so the browser never receives `ELEVENLABS_API_KEY`.
- **MCP** — `scripts/mcp_telecom.py` exposes the telecom mock over stdio. Hosted ElevenLabs MCP is a different product; see [mcp-lab-server.md](mcp-lab-server.md).
- **Post-call data** — This repo does not run a long-lived **post-call webhook** HTTP receiver. Recent conversations can be inspected with [`scripts/conversations_list.py`](../scripts/conversations_list.py); for a production-style webhook design, see [Post-call webhooks pattern](patterns/post-call-webhooks.md).

## Going further

When you have walked through the demo and want **ideas for what to try next** (still as learning, not as shipping this repo as a product), see [Extending this lab](extending-this-lab.md).
