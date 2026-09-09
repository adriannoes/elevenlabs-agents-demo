# Telecom — Customer Care Demo

Storytelling for the **Telecom Customer Care** Brazilian-domain scenario (`eleven_demo.scenarios.telecom`; conversation language is English). Used by the Gradio **Telecom** tab and linked from the repository walkthrough.

## Persona

**Maria**, 38, calls the carrier on her lunch break: intermittent mobile data, a confusing line item on the bill, and occasional need for package changes. She expects the IVR to hand off to something that sounds human, understands Brazilian Portuguese, and pulls up her account without making her repeat information endlessly.

**Operations / product** stakeholders care about first-contact resolution for tier-one telecom topics, shorter handle time on repetitive queries, and a clean path to a human agent when the topic is regulatory, legal, or out of scope — without leaking full CPF or account identifiers into client-side logs or demo UIs.

## Problem space

Brazilian carriers run high-volume SAC with strict LGPD expectations around CPF and account data. Voice assistants must combine low-latency ASR/TTS with **server-side tools** that return account context only after validated input. Industry benchmarks vary by operator; this demo does not embed proprietary SLAs — it encodes the **pattern**: identity check → tool-backed lookup → scripted escalation.

Constraints reflected in code:

- **English** conversation with voice-friendly prompts (no long markdown lists in the agent reply style); CPF and account facts stay in the Brazilian domain.
- **Mock** `lookup_telecom_account` and `transfer_to_human` tools; production-shaped PSTN handoff would use the platform [**Transfer to number**](https://elevenlabs.io/docs/eleven-agents/customization/tools/system-tools/transfer-to-number) system tool instead.

## Demo flow

1. **Provision**
   Run `uv run python scripts/agent_create.py telecom`, then set `DEMO_AGENT_ID_TELECOM` in `.env` (see `product/guides/demo-agent-setup.md`).

2. **Gradio**
   Start `uv run python apps/gradio_app.py`, open the **Telecom** tab, click **Start session**. The widget loads via an **HTTPS signed conversation URL** so the raw `agent_id` is not a public embed constant.

3. **Conversation**
   Speak in English. The agent asks for CPF (11 digits); after a valid CPF it may call the lookup tool. Off-topic or sensitive cases should route toward human transfer per the system prompt.

4. **Observability**
   Inspect transcripts and tool behavior in ElevenLabs [**Agent Testing**](https://elevenlabs.io/docs/eleven-agents/customization/agent-testing) or the product dashboard — not inside Gradio chrome.

5. **Optional React surface**
   If your clone includes `apps/web/`, `pnpm --dir apps/web dev` exercises the same `agent_id` with [`elevenlabs/ui`](https://github.com/elevenlabs/ui) and a server-side signed-URL route.

A screenshot of this tab (signed-URL session + official widget) lives in the README (section "Run the demo (Gradio)"). Do not embed that image here — Gradio loads this file into the tab.

## ROI hypothesis

Illustrative framing only — calibrate with your own AHT, volume, and labor rates:

| Signal | Direction if voice agent works |
| --- | --- |
| **Containment** for bill / package / signal triage | ↑ fewer live-agent touches on repeatable intents |
| **AHT** on tier-one SAC | ↓ faster account context via tools vs. manual CRM lookup |
| **CSAT / NPS** | ↑ when latency and clarity match caller expectations |

**Back-of-envelope** (replace variables):
`monthly_savings ≈ calls_contained × (avg_agent_minutes_saved / 60) × blended_hourly_cost − platform_cost`.
The demo proves **technical feasibility** of the path (voice + tools + signed embed), not a validated financial model.

## Talking points

- **Signed URL as trust boundary** — mirrors how teams keep API keys and agent IDs off public pages while still shipping the official embed.
- **Server tools for PII** — lookups stay on the server; the widget is conversation UI, not a CRM replacement.
- **Idempotent provisioning** — `upsert_agent` by stable agent name avoids duplicate agents on every demo run.
- **English conversation, Brazilian domain** — agent copy is English; CPF / BRL stay in the scenario. TTS playground voices still default to PT-BR via `DEFAULT_PT_VOICE_ID`.
- **Escalation story** — demo uses `transfer_to_human`; production often uses **transfer_to_number** for PSTN/SIP.

## Risks and mitigations

- **Risk**: Verbatim CPF or account details in logs, transcripts, or screenshots. **Mitigation**: redact in observability; follow workspace logging rules; mask in prompts (`telecom.py` instructs masking in voice).
- **Risk**: Overstating containment or cost savings from a mocked tool stack. **Mitigation**: label ROI as hypothesis; separate demo from production integrations and real CRM data.
- **Risk**: Widget or signed-URL misconfiguration exposes configuration drift between Gradio and `apps/web`. **Mitigation**: single `DEMO_AGENT_ID_TELECOM`; document env parity in `apps/web/README.md`.

## References

- [ElevenAgents overview](https://elevenlabs.io/docs/eleven-agents/overview)
- [Integrate / embed](https://elevenlabs.io/docs/eleven-agents/integrate/overview)
- [Agent Testing](https://elevenlabs.io/docs/eleven-agents/customization/agent-testing)
- [Transfer to number (system tool)](https://elevenlabs.io/docs/eleven-agents/customization/tools/system-tools/transfer-to-number)
- [Models](https://elevenlabs.io/docs/overview/models) (TTS/STT defaults)
- Repository: `src/eleven_demo/scenarios/telecom.py`, `scripts/agent_create.py`, `apps/gradio_app.py`, optional `apps/web/`
