# Healthcare — Triage Demo

Storytelling for the **Healthcare Triage** Brazilian-domain scenario (`eleven_demo.scenarios.healthcare`; conversation language is English). Used by the Gradio **Healthcare** tab and linked from the repository walkthrough.

## Persona

**Ana**, 51, has had a fever for two days and is unsure whether she should schedule a routine appointment or seek urgent care. She wants fast guidance in Portuguese; in this lab the agent replies in English. She does not want a voice assistant to diagnose her, prescribe medication, or repeat sensitive health details out loud.

**Clinical operations, compliance, and product** stakeholders care about a different question: can a voice agent use approved internal guidance, stay inside triage boundaries, surface the source documents behind its behavior, and escalate when symptoms suggest emergency care or ambiguity?

## Problem space

Healthcare voice flows are high-trust, high-risk interactions. The assistant must be helpful without sounding like a clinician making a definitive diagnosis. It should retrieve narrow, approved guidance from a knowledge base, suggest organizational next steps, and escalate quickly when symptoms may be urgent.

Constraints reflected in code:

- **RAG-backed guidance** — `healthcare.py` uploads six Markdown seed files from `data/kb/healthcare/`, computes a RAG index, and attaches the document IDs to the agent prompt with `usage_mode="auto"`.
- **Limited tools** — the scenario exposes only `book_medical_appointment` and `transfer_to_human`; it does not expose diagnosis, prescription, lab-result interpretation, or insurance authorization tools.
- **Zero Retention Mode** — provisioning sends `platform_settings.privacy.zero_retention_mode=True`, matching the medical-data posture used by the Banking scenario.

## Knowledge base seeds

The seed files are fictional, English-language documents that make the RAG behavior visible without using real patient data:

| File | Role in the demo |
| --- | --- |
| `01-symptom-fever.md` | Fever triage language, escalation signals, and safe specialty suggestions for prolonged fever. |
| `02-symptom-headache.md` | Headache guidance, emergency red flags, and Neurology / Clinical Medicine routing language. |
| `03-symptom-chest-pain.md` | Chest-pain safety-first guidance; new non-trivial chest pain should trigger emergency escalation. |
| `04-specialties.md` | Fictional specialty map and business-hour caveats for organizational next steps. |
| `05-lgpd-policy.md` | Demo privacy posture for sensitive health data, Brazilian LGPD (Art. 11) framing, minimization, and ZRM caveats. Clarifies that this line does **not** use CPF authentication. |
| `06-demo-conversation-cues.md` | Fictional English lines for triage-only vs `VITA-####` + morning/afternoon booking smoke tests (no real identifiers). |

Provisioning flow:

1. `healthcare_kb_seed_paths()` resolves the six files under `data/kb/healthcare/` and fails fast if any seed is missing.
2. `ensure_kb_file_uploaded()` reuses an existing KB document when the name matches; otherwise it uploads the file.
3. `compute_rag(doc_ids)` requests RAG indexes with the default `multilingual_e5_large_instruct` embedding model.
4. `Scenario._build_conversation_config()` attaches each document ID under `prompt.knowledge_base` so the agent can retrieve context automatically.
5. `upsert_agent()` creates or updates the `demo-healthcare-triage-en` agent with ZRM platform settings.

The first Healthcare provisioning run can be slower than Telecom or Banking because it uploads documents and builds indexes. Later runs should reuse documents by name.

## Demo flow

1. **Provision**
   Run `uv run python scripts/agent_create.py healthcare`, then set `DEMO_AGENT_ID_HEALTHCARE` in `.env` (see `product/guides/demo-agent-setup.md`).

2. **Gradio**
   Start `uv run python apps/gradio_app.py`, open the **Healthcare** tab, and click **Start session**. The widget loads through a signed conversation URL.

3. **Source documents**
   The Healthcare tab also renders a source-documents panel from `SCENARIO.kb_doc_ids`, making the RAG setup visible to reviewers instead of hiding it inside the remote agent configuration.

4. **Conversation**
   Speak in **English** with the configured agent. Describe a symptom (for example: "I've had a high fever for two days with a cough") for triage-only guidance. To exercise **booking**, say a fictional token such as **VITA-1001** plus **morning** or **afternoon** — there is no CPF lookup in this sandbox; do not add real CPF to the knowledge base.

5. **Observability**
   Use ElevenLabs Agent Testing or the dashboard to inspect behavior when retention settings allow it. With ZRM-enabled flows, plan a compliant post-call webhook or downstream event stream if operational records are required.

<!-- Screenshot placeholders (replace after capture): -->
<!-- ![Healthcare tab — before session](docs/assets/healthcare-tab-idle.png) -->
<!-- ![Healthcare tab — RAG source panel](docs/assets/healthcare-tab-sources.png) -->

## Compliance and privacy posture

This repository is a technical demo, not clinical validation, HIPAA certification, or legal advice.

- **LGPD and sensitive health data** — health data receives special treatment under LGPD. The demo uses fictional seeds, avoids real patient identifiers, and instructs the agent not to repeat CPF, medical-record numbers, or detailed diagnoses unnecessarily.
- **No automated clinical decision** — the scenario is limited to educational triage language and routing. It does not diagnose, prescribe, or replace a licensed professional.
- **Zero Retention Mode** — ZRM reduces platform-side retained conversation data for this agent, but it also reduces debugging visibility. It is a data-minimization control, not a complete compliance program by itself.
- **Source control hygiene** — seed files must remain fictional. Do not add real patient transcripts, CPF, phone numbers, insurance IDs, prescriptions, or clinical records to `data/kb/healthcare/`.

## ROI hypothesis

Illustrative framing only — calibrate with real triage volume, clinician review policy, escalation rates, and appointment availability:

| Signal | Direction if voice agent works |
| --- | --- |
| **Appropriate routing** for low-acuity questions | ↑ clearer next step before live staff involvement |
| **Emergency escalation consistency** | ↑ safer handling of high-risk symptom language |
| **Operational load** on front desk / nurse line | ↓ fewer repetitive scheduling and specialty-routing questions |
| **Policy adherence** | ↑ approved KB language is reused instead of improvised by the assistant |

**Back-of-envelope** (replace variables):
`monthly_value ≈ triage_cases_deflected × avg_minutes_saved × blended_staff_cost_per_minute − platform_and_governance_costs`.
The demo proves the **RAG + voice + escalation pattern**, not clinical or financial outcomes.

## Talking points

- **RAG makes source material inspectable** — the source panel and seed files show what the assistant had available.
- **Safety-first prompt boundary** — the agent is told not to diagnose or prescribe, and to escalate urgent symptoms.
- **Small documents beat broad dumping** — six focused Markdown seeds are easier to review, update, and reason about than one large policy blob.
- **ZRM for medical PII** — the scenario intentionally trades off stored conversation history for data minimization.
- **Healthcare is server-side state** — the RAG behavior lives in the ElevenLabs agent configuration, so the Gradio UI displays sources but does not implement retrieval itself.

## Risks and mitigations

- **Risk**: Users may interpret educational triage language as medical advice. **Mitigation**: keep copy non-diagnostic, include emergency escalation, and state that the demo does not replace clinical evaluation.
- **Risk**: Real patient data is accidentally added to KB seeds or screenshots. **Mitigation**: keep seeds fictional, review generated artifacts, and redact before sharing.
- **Risk**: RAG returns plausible but incomplete guidance. **Mitigation**: keep documents narrow, test common symptom prompts, and route ambiguity to `transfer_to_human`.
- **Risk**: ZRM removes conversation history needed for debugging. **Mitigation**: rely on unit tests, simulated conversations, and explicitly designed post-call events if records are required.

## References

- [ElevenAgents overview](https://elevenlabs.io/docs/eleven-agents/overview)
- [Knowledge base](https://elevenlabs.io/docs/eleven-agents/customization/knowledge-base)
- [Zero Retention Mode per agent](https://elevenlabs.io/docs/eleven-agents/customization/privacy/zrm)
- [Conversation history redaction](https://elevenlabs.io/docs/eleven-agents/customization/privacy/conversation-history-redaction)
- [Data residency](https://elevenlabs.io/docs/overview/administration/data-residency)
- [Brazilian LGPD (full text in Portuguese)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- Repository: `src/eleven_demo/scenarios/healthcare.py`, `src/eleven_demo/agents/kb.py`, `data/kb/healthcare/`, `scripts/agent_create.py`, `apps/gradio_app.py`
