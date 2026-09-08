# Banking — Digital Banking Demo

Storytelling for the **Digital Banking** Brazilian-domain scenario (`eleven_demo.scenarios.banking`; conversation language is English). Used by the Gradio **Banking** tab and linked from the repository walkthrough.

## Persona

**Rafael**, 42, notices an unfamiliar card transaction while commuting. He wants to check account status, block a card if needed, and understand whether a human specialist should take over. He expects a calm Portuguese voice assistant; in this lab the agent replies in English. He also expects the bank to authenticate him before revealing account details or taking card actions.

**Risk, compliance, and product** stakeholders care less about a flashy voice demo and more about the control pattern: identity verification before tools, masked outputs, human escalation for fraud or disputes, and data minimization for financial PII.

## Problem space

Banking voice flows combine money movement, identity data, and regulatory obligations. A useful demo must therefore show restraint: the assistant can answer high-level account questions and initiate mocked card workflows only after staged authentication. It must not promise refunds, investments, loans, or final dispute outcomes.

Constraints reflected in code:

- **Authentication before tools** — `banking.py` requires CPF plus an approximate last-transaction amount before `lookup_account_summary`, `request_card_block`, or `request_card_replacement`.
- **Masked server-tool outputs** — the mock tools return masked account and ticket references; the voice prompt instructs the agent not to repeat unnecessary sensitive data.
- **Zero Retention Mode** — provisioning sends `platform_settings.privacy.zero_retention_mode=True`, matching the higher-risk PII posture required by this scenario.

## Demo flow

1. **Provision**
   Run `uv run python scripts/agent_create.py banking`, then set `DEMO_AGENT_ID_BANKING` in `.env` (see `product/guides/demo-agent-setup.md`).

2. **Gradio**
   Start `uv run python apps/gradio_app.py`, open the **Banking** tab, and click **Start session**. The widget loads through a signed conversation URL; the raw API key and agent configuration remain server-side.

3. **Conversation**
   Speak in English. The first message asks for CPF and an approximate last movement amount. After those inputs, ask for a balance summary or card block/replacement. For fraud, regulatory disputes, or ambiguous requests, the agent should offer `transfer_to_human`.

4. **Privacy posture**
   The Banking agent is provisioned with per-agent Zero Retention Mode. That means no stored call recording, transcript, or post-call metadata containing PII should be retained by ElevenLabs systems for that agent; debugging should rely on controlled test runs or downstream systems you explicitly operate.

5. **Observability**
   Use ElevenLabs Agent Testing or the dashboard for functional inspection when ZRM is not preventing history review. For ZRM-enabled production-style flows, plan a compliant post-call webhook if you need operational records.

<!-- Screenshot placeholders (replace after capture): -->
<!-- ![Banking tab — before session](docs/assets/banking-tab-idle.png) -->
<!-- ![Banking tab — authenticated flow](docs/assets/banking-tab-authenticated.png) -->

## Compliance posture

This repository is a technical demo, not a compliance certification. The scenario is designed to make the right questions visible:

- **BACEN / Open Finance** — customer financial data should be accessed only with clear user context and appropriate authorization. This demo does not implement Open Finance consent or regulated payment operations; it demonstrates a voice front end around mocked account tools.
- **LGPD** — CPF, account information, and conversation content are personal data. The demo minimizes echoing sensitive values, uses mocked data, and enables ZRM for the agent. Real deployments still need lawful basis, data-subject rights handling, retention policy, vendor review, and incident response.
- **PCI-DSS** — the demo does not collect full PAN, CVV, PIN, or sensitive authentication data. Card actions use masked references only. Any real cardholder-data environment must be assessed against PCI-DSS and must keep voice, transcript, logging, and tool integrations out of scope or properly controlled.
- **Zero Retention Mode** — ZRM reduces platform-side retained data, but it also limits debugging and conversation-history review. If a bank needs audit evidence, it should capture only the necessary post-call events in its own secured, redacted, access-controlled systems.

## ROI hypothesis

Illustrative framing only — calibrate with real contact-center volume, fraud queues, compliance review time, and escalation rates:

| Signal | Direction if voice agent works |
| --- | --- |
| **Tier-one containment** for account status and card logistics | ↑ fewer live-agent touches for repeatable authenticated intents |
| **Fraud triage time** | ↓ faster routing once the assistant identifies dispute or fraud language |
| **Compliance confidence** | ↑ when authentication, masking, ZRM, and escalation are explicit rather than implicit |

**Back-of-envelope** (replace variables):
`monthly_value ≈ authenticated_self_service_cases × avg_minutes_saved × blended_cost_per_minute − platform_and_control_costs`.
The demo proves **workflow shape** and security posture, not production ROI.

## Talking points

- **Security-first prompt design** — the agent must authenticate before any banking tool and must escalate on disputes or unclear requests.
- **Server tools as control points** — financial actions are mocked behind typed tools, keeping browser UI separate from sensitive business logic.
- **ZRM for high-risk PII** — the scenario intentionally trades off platform conversation history for data minimization.
- **PCI-DSS boundary** — no full card number, CVV, or PIN enters the demo flow; masked references keep the example outside a real cardholder-data environment.
- **Voice biometrics are out of scope** — the demo uses conversational authentication prompts only; biometric enrollment, matching, consent, and spoofing defenses would be a separate product and compliance effort.

## Risks and mitigations

- **Risk**: Users may treat a mocked card block as a production-grade fraud workflow. **Mitigation**: label tool outputs as demo tickets; route disputes and fraud to `transfer_to_human`.
- **Risk**: Financial PII appears in screenshots, transcripts, logs, or generated reports. **Mitigation**: use fictional data, mask references, enable ZRM, and redact any manually captured evidence.
- **Risk**: ZRM removes useful debugging artifacts. **Mitigation**: keep deterministic unit and simulated-conversation tests, and design a separate secured post-call event stream if operational records are required.
- **Risk**: Compliance language overclaims readiness. **Mitigation**: present BACEN, LGPD, and PCI-DSS as review areas and control boundaries, not as certifications.

## References

- [ElevenAgents overview](https://elevenlabs.io/docs/eleven-agents/overview)
- [Zero Retention Mode per agent](https://elevenlabs.io/docs/eleven-agents/customization/privacy/zrm)
- [Conversation history redaction](https://elevenlabs.io/docs/eleven-agents/customization/privacy/conversation-history-redaction)
- [Data residency](https://elevenlabs.io/docs/overview/administration/data-residency)
- [Banco Central do Brasil — Open Finance](https://www.bcb.gov.br/estabilidadefinanceira/openfinance)
- [Brazilian LGPD (full text in Portuguese)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- [PCI Security Standards](https://www.pcisecuritystandards.org/standards/)
- Repository: `src/eleven_demo/scenarios/banking.py`, `src/eleven_demo/agents/tools.py`, `scripts/agent_create.py`, `apps/gradio_app.py`
