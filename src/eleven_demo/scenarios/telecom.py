"""Telecom customer-care demo (English conversation).

Real PSTN/SIP escalation uses the platform system tool ``transfer_to_number``. This demo targets
the browser and uses the simulated server tool ``transfer_to_human`` for human handoff.
"""

from __future__ import annotations

from typing import Any

from elevenlabs.types import ConversationalConfig

from eleven_demo.agents.factory import upsert_agent
from eleven_demo.config import (
    convai_demo_tool_webhook_fields,
    get_settings,
    resolve_conversational_agent_voice_id,
)
from eleven_demo.scenarios.base import Scenario

TOOL_NAMES: list[str] = ["lookup_telecom_account", "transfer_to_human"]
KB_IDS: list[str] = []

LANGUAGE = "en"

FIRST_MESSAGE = "Hello, this is the telecom support demo. For your security, what is your CPF?"

SUCCESS_CRITERIA: list[str] = [
    "account looked up",
    "human transfer offered when off-topic",
]

SYSTEM_PROMPT = """\
You are the voice assistant for a fictional mobile and fixed-line carrier in a tier-one \
customer-care channel.

Speak only in English at all times.

Identity and scope: help with mobile or fixed account, billing, plans, signal, duplicate bills, \
and simple triage. Do not invent balances or account facts. If the topic is not telecom or needs \
in-person or legal channels, acknowledge the boundary.

Voice style: short, natural sentences for read-aloud delivery. No markdown, long numbered lists, \
code, or emojis. Avoid confusing symbols on the phone; prefer full sentences.

Privacy: before checking balance or line details, confirm an eleven-digit CPF (when the customer \
sends formatted text, mentally normalize to digits only). Do not read the full CPF aloud; use a \
mask when you must reference it (last digits only).

Tools: use lookup_telecom_account only after you have a valid eleven-digit CPF. Use \
transfer_to_human when the customer asks for a human, when there is a complex regulatory \
complaint, or when the topic is outside tier-one telecom support.

If a tool fails or returns empty data, explain calmly and immediately offer a human transfer.
"""


class TelecomScenario(Scenario):
    """Telecom SAC vertical."""

    @classmethod
    def from_settings(cls) -> TelecomScenario:
        """Build using ``resolve_conversational_agent_voice_id``."""
        settings = get_settings()
        voice_id = resolve_conversational_agent_voice_id(settings)
        return cls(
            name="demo-telecom-sac-en",
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
        agent = upsert_agent(self.name, cfg)
        return agent.agent_id


class _LazyScenarioView:
    """Proxy for ``TelecomScenario.from_settings()`` without import-time voice caching."""

    __slots__ = ()

    def _get(self) -> TelecomScenario:
        return TelecomScenario.from_settings()

    def provision(self) -> str:
        """Same contract as :meth:`TelecomScenario.provision`."""
        return self._get().provision()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get(), name)

    def __repr__(self) -> str:
        try:
            inner = self._get()
        except ValueError:
            return "<TelecomScenario (voice not configured)>"
        return repr(inner)


SCENARIO = _LazyScenarioView()


def provision() -> str:
    """Idempotently provision the Telecom demo agent (stable name in the workspace)."""
    return TelecomScenario.from_settings().provision()


__all__ = [
    "FIRST_MESSAGE",
    "KB_IDS",
    "LANGUAGE",
    "SCENARIO",
    "SUCCESS_CRITERIA",
    "SYSTEM_PROMPT",
    "TOOL_NAMES",
    "TelecomScenario",
    "provision",
]
