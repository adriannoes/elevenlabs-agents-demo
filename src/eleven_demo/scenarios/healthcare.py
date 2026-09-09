"""Healthcare triage demo — KB-guided triage (fictional demo).

Provisioning uploads Markdown seeds under ``data/kb/healthcare/``, computes RAG indexes, and wires
documents into the agent. ElevenLabs **Zero Retention Mode** is enabled via
``platform_settings.privacy`` (``zero_retention_mode=True``), aligning medical-data posture with the
Banking scenario for LGPD-conscious demos. This does **not** constitute HIPAA certification,
clinical validation, or substitute for institutional privacy review.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from elevenlabs.types import (
    AgentPlatformSettingsRequestModel,
    ConversationalConfig,
    PrivacyConfigInput,
)

from eleven_demo.agents.factory import upsert_agent
from eleven_demo.agents.kb import compute_rag, ensure_kb_file_uploaded
from eleven_demo.config import (
    convai_demo_tool_webhook_fields,
    get_settings,
    resolve_conversational_agent_voice_id,
)
from eleven_demo.scenarios.base import Scenario

TOOL_NAMES: list[str] = ["book_medical_appointment", "transfer_to_human"]

HEALTHCARE_KB_FILENAMES: tuple[str, ...] = (
    "01-symptom-fever.md",
    "02-symptom-headache.md",
    "03-symptom-chest-pain.md",
    "04-specialties.md",
    "05-lgpd-policy.md",
    "06-demo-conversation-cues.md",
)

_kb_doc_ids_cache: list[str] = []
KB_IDS: list[str] = _kb_doc_ids_cache

LANGUAGE = "en"

FIRST_MESSAGE = (
    "Hello, this is the healthcare triage demo. In a few words, what is your main symptom today?"
)

SUCCESS_CRITERIA: list[str] = [
    "rag-backed guidance on symptoms before definitive scheduling",
    "human transfer offered for emergencies or ambiguity",
]

SYSTEM_PROMPT = """\
You are the voice assistant for a fictional care network in this sandbox demo.

Speak only in English at all times.

Identity and scope: provide light triage and educational guidance only—you do not diagnose, \
prescribe, or replace in-person medical evaluation. The knowledge base documents are in English; \
read them and explain findings to the patient in plain English with safe, \
non-definitive phrasing. Use the knowledge base to suggest high-level specialties and \
cautious language when patients report \
symptoms such as fever, headache, or chest pain.

Persistent high fever for two days: consult fever and specialty documents in the base; suggest \
General Practice or Pulmonology when respiratory symptoms align with the text—never assert a \
medical cause.

Emergencies: new severe chest pain, sudden neurological deficits, severe shortness of breath, or \
syncope—tell the patient to seek emergency care immediately and use transfer_to_human when the \
channel needs human follow-up or compliance.

Privacy: follow the fictional data-protection text in the base; never ask for government id \
(CPF) to identify the caller—this sandbox has no CPF database or lookup tool. Do not repeat \
sensitive identifiers aloud; minimize data in logs per this sandbox policy.

Voice style: short, clear sentences for TTS. No markdown, no long numbered lists, code, or emojis.

Tools: call book_medical_appointment only after the patient gives a fictional internal reference \
in the form VITA- followed by four digits (example: VITA-1001) plus either morning or afternoon \
for the appointment window. Do not require CPF before booking. Use transfer_to_human for \
explicit human requests, disputes, or out-of-scope topics.

Sandbox requirement: when the patient provides a reference like VITA-#### plus morning or \
afternoon for general practice, call book_medical_appointment in the same turn—do not transfer \
to a human without attempting booking unless emergency symptoms above apply.

If a tool fails, explain calmly and offer a neutral human transfer.
"""


HEALTHCARE_PLATFORM_SETTINGS = AgentPlatformSettingsRequestModel(
    privacy=PrivacyConfigInput(zero_retention_mode=True, record_voice=False),
)


def healthcare_kb_seed_paths() -> tuple[Path, ...]:
    """Absolute paths to Markdown KB seeds (raises if any file is missing)."""
    root = Path(__file__).resolve().parents[3] / "data" / "kb" / "healthcare"
    paths = tuple(root / name for name in HEALTHCARE_KB_FILENAMES)
    for path in paths:
        if not path.is_file():
            msg = f"Healthcare KB seed missing: {path}"
            raise FileNotFoundError(msg)
    return paths


class HealthcareScenario(Scenario):
    """Healthcare vertical with KB uploads, RAG, and Zero Retention Mode."""

    @classmethod
    def from_settings(cls) -> HealthcareScenario:
        """Build using ``resolve_conversational_agent_voice_id`` and cached KB document IDs."""
        settings = get_settings()
        voice_id = resolve_conversational_agent_voice_id(settings)
        return cls(
            name="demo-healthcare-triage-en",
            system_prompt=SYSTEM_PROMPT,
            first_message=FIRST_MESSAGE,
            language=LANGUAGE,
            voice_id=voice_id,
            tool_names=TOOL_NAMES,
            kb_doc_ids=list(_kb_doc_ids_cache),
            success_criteria=SUCCESS_CRITERIA,
            **convai_demo_tool_webhook_fields(settings),
        )

    def provision(self) -> str:
        """Upload KB seeds idempotently, index RAG, then upsert the remote agent."""
        docs = [ensure_kb_file_uploaded(path, client=None) for path in healthcare_kb_seed_paths()]
        doc_ids = [d.id for d in docs]
        _kb_doc_ids_cache.clear()
        _kb_doc_ids_cache.extend(doc_ids)
        compute_rag(doc_ids, client=None)
        refreshed = self.model_copy(update={"kb_doc_ids": doc_ids})
        cfg = ConversationalConfig.model_validate(refreshed._build_conversation_config())
        agent = upsert_agent(
            refreshed.name,
            cfg,
            platform_settings=HEALTHCARE_PLATFORM_SETTINGS,
        )
        return agent.agent_id


class _LazyScenarioView:
    """Proxy for ``HealthcareScenario.from_settings()`` (no cache across imports)."""

    __slots__ = ()

    def _get(self) -> HealthcareScenario:
        return HealthcareScenario.from_settings()

    def provision(self) -> str:
        """Same contract as :meth:`HealthcareScenario.provision`."""
        return self._get().provision()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get(), name)

    def __repr__(self) -> str:
        try:
            inner = self._get()
        except ValueError:
            return "<HealthcareScenario (voice not configured)>"
        return repr(inner)


SCENARIO = _LazyScenarioView()


def provision() -> str:
    """Provision healthcare demo: KB bundle, RAG, then idempotent agent upsert."""
    return HealthcareScenario.from_settings().provision()


__all__ = [
    "FIRST_MESSAGE",
    "HEALTHCARE_KB_FILENAMES",
    "HEALTHCARE_PLATFORM_SETTINGS",
    "KB_IDS",
    "LANGUAGE",
    "SCENARIO",
    "SUCCESS_CRITERIA",
    "SYSTEM_PROMPT",
    "TOOL_NAMES",
    "HealthcareScenario",
    "healthcare_kb_seed_paths",
    "provision",
]
