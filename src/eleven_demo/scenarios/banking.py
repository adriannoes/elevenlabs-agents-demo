"""Banking assistant demo (English voice and conversation).

Provisioning enables ElevenLabs **Zero Retention Mode** via ``platform_settings.privacy``
(``zero_retention_mode=True``), reducing persistent storage of conversational PII as described in
the Agents Platform privacy model. This demo posture supports privacy-conscious storytelling;
it does not replace legal review, financial oversight, or PCI-DSS controls for production systems.
"""

from __future__ import annotations

from typing import Any

from elevenlabs.types import (
    AgentPlatformSettingsRequestModel,
    ConversationalConfig,
    PrivacyConfigInput,
)

from eleven_demo.agents.factory import upsert_agent
from eleven_demo.config import (
    convai_demo_tool_webhook_fields,
    get_settings,
    resolve_conversational_agent_voice_id,
)
from eleven_demo.scenarios.base import Scenario

TOOL_NAMES: list[str] = [
    "lookup_account_summary",
    "request_card_block",
    "request_card_replacement",
    "transfer_to_human",
]
KB_IDS: list[str] = []

# Convai ``language``: English ASR/TTS for this vertical.
LANGUAGE = "en"

FIRST_MESSAGE = (
    "Hello, this is the digital banking demo. For your security, please provide your CPF and the "
    "approximate amount of your last transaction in the local currency."
)

SUCCESS_CRITERIA: list[str] = [
    "authentication completed before account tools",
    "human transfer offered for disputes or out of scope",
]

SYSTEM_PROMPT = """\
You are the voice assistant for a fictional payments institution in this sandbox demo.

Speak only in English at all times—every reply to the customer, including tool narration and \
apologies.

Identity and scope: help only with high-level account questions, card block, or card replacement \
after confirmation. Do not promise investments, loans, or final chargebacks. If the customer asks \
for anything outside this scope, state the limit clearly and offer transfer_to_human.

Mandatory authentication: before calling lookup_account_summary, request_card_block, or \
request_card_replacement you must have (1) a valid eleven-digit CPF and (2) a customer-provided \
reference amount for their latest movement in BRL (it does not need to match to the cent, but it \
must be plausible). If either is missing, ask politely before using tools.

Voice style: short, clear answers for TTS. No markdown, no long bullet lists, no code, no emojis. \
Avoid reading long numbers monotonically; group digits naturally when possible.

Privacy and security: do not echo sensitive data unnecessarily; never confirm full card numbers—\
only use masks returned by tools. For regulatory disputes, open fraud, or ambiguous requests, \
prefer transfer_to_human.

If a tool fails, explain briefly and offer a calm human transfer.
"""


BANKING_PLATFORM_SETTINGS = AgentPlatformSettingsRequestModel(
    privacy=PrivacyConfigInput(zero_retention_mode=True, record_voice=False),
)


class BankingScenario(Scenario):
    """Banking vertical with Zero Retention Mode policy on the agent."""

    @classmethod
    def from_settings(cls) -> BankingScenario:
        """Build using ``resolve_conversational_agent_voice_id`` (voice fallbacks in config)."""
        settings = get_settings()
        voice_id = resolve_conversational_agent_voice_id(settings)
        return cls(
            name="demo-banking-sac-en",
            system_prompt=SYSTEM_PROMPT,
            first_message=FIRST_MESSAGE,
            language=LANGUAGE,
            voice_id=voice_id,
            tool_names=TOOL_NAMES,
            kb_doc_ids=KB_IDS,
            success_criteria=SUCCESS_CRITERIA,
            **convai_demo_tool_webhook_fields(settings),
        )

    def provision(self) -> str:
        """Create or update the remote agent and return ``agent_id``."""
        cfg = ConversationalConfig.model_validate(self._build_conversation_config())
        agent = upsert_agent(
            self.name,
            cfg,
            platform_settings=BANKING_PLATFORM_SETTINGS,
        )
        return agent.agent_id


class _LazyScenarioView:
    """Proxy for ``BankingScenario.from_settings()`` (no cache)."""

    __slots__ = ()

    def _get(self) -> BankingScenario:
        return BankingScenario.from_settings()

    def provision(self) -> str:
        """Same contract as :meth:`BankingScenario.provision`."""
        return self._get().provision()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get(), name)

    def __repr__(self) -> str:
        try:
            inner = self._get()
        except ValueError:
            return "<BankingScenario (voice not configured)>"
        return repr(inner)


SCENARIO = _LazyScenarioView()


def provision() -> str:
    """Idempotently provision the banking demo agent."""
    return BankingScenario.from_settings().provision()


__all__ = [
    "BANKING_PLATFORM_SETTINGS",
    "FIRST_MESSAGE",
    "KB_IDS",
    "LANGUAGE",
    "SCENARIO",
    "SUCCESS_CRITERIA",
    "SYSTEM_PROMPT",
    "TOOL_NAMES",
    "BankingScenario",
    "provision",
]
