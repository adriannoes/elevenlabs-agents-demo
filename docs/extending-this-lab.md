# Extending this lab

You have run the [walkthrough](walkthrough.md) and explored the [Gradio app](../README.md#run-the-demo-gradio). This page lists **learning-oriented** directions—ways to keep experimenting with ElevenLabs—not a commitment to turn this repository into a shipping product.

## Already in the lab (start here)

- **MCP stdio** — [`docs/mcp-lab-server.md`](mcp-lab-server.md). Next step: expose the same mock over an HTTP MCP transport behind a tunnel and attach it to the Telecom agent as an external MCP tool (stdio cannot be attached).
- **Skills vs Models drift** — `uv run python scripts/skills_model_drift.py`. Next step: send the patch in [`docs/upstream-skills-notes.md`](upstream-skills-notes.md) to `elevenlabs/skills` if the live diff still fails.
- **Pitfalls** — [`docs/pitfalls.md`](pitfalls.md). Next step: add one more fixture when you hit a new live-API contract.

## Telephony and CRM

Voice agents often terminate on **PSTN or SIP** and hand outcomes to a **CRM**. The public docs cover telephony providers; this repo stays UI- and script-first. A natural next step is a small spike that registers the same agent id with a test number and records call ids in a notebook or spreadsheet.

## Observability

The library already surfaces **request metadata** where the SDK allows it (for example TTS character counts and request ids). A useful exercise is to thread those fields into structured logs in a throwaway branch and compare latency percentiles across regions or models—still in a lab setting, not as a managed observability product.

## Signed webhooks

Server tools and **post-call webhooks** both require trusting HTTP callbacks. The [post-call webhooks pattern](patterns/post-call-webhooks.md) summarizes verification and redaction. Implementing a minimal verified receiver in another repo (or a local tunnel) is a good way to learn the failure modes without coupling them to this playground.

## Agent evaluation

Beyond ad hoc chats in Gradio, you can run scripted multi-turn simulations from the CLI (see `--messages-file` on [`scripts/agent_simulate.py`](../scripts/agent_simulate.py) and the walkthrough). Larger **evaluation datasets** and regression runs are a separate topic; start with a handful of JSON fixtures that encode realistic user turns.

## This repo vs production code

Keep a bright line: **this repository** is for study, reproducible scripts, and documentation. Production systems add tenancy, key rotation, incident response, and data governance that are intentionally out of scope here.
