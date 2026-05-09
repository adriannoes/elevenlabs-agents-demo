"""Demo scenario names and mapping from CLI labels to settings / env keys."""

from __future__ import annotations

from typing import Final

from eleven_demo.config import Settings

DEMO_SCENARIOS: Final[tuple[str, ...]] = ("telecom", "banking", "healthcare")

SCENARIO_TO_SETTINGS_FIELD: Final[dict[str, str]] = {
    "telecom": "demo_agent_id_telecom",
    "banking": "demo_agent_id_banking",
    "healthcare": "demo_agent_id_healthcare",
}

SCENARIO_TO_DEMO_ENV_KEY: Final[dict[str, str]] = {
    "telecom": "DEMO_AGENT_ID_TELECOM",
    "banking": "DEMO_AGENT_ID_BANKING",
    "healthcare": "DEMO_AGENT_ID_HEALTHCARE",
}


class MissingDemoAgentIdError(ValueError):
    """Raised when a ``DEMO_AGENT_ID_*`` value is missing for a scenario."""

    def __init__(self, scenario: str, env_key: str) -> None:
        self.scenario = scenario
        self.env_key = env_key
        super().__init__(env_key)


def require_demo_agent_id(settings: Settings, scenario: str) -> str:
    """Return the configured agent id for ``scenario`` or raise ``MissingDemoAgentIdError``."""
    if scenario not in SCENARIO_TO_SETTINGS_FIELD:
        raise KeyError(scenario)
    field = SCENARIO_TO_SETTINGS_FIELD[scenario]
    raw = getattr(settings, field)
    if raw is None or not str(raw).strip():
        raise MissingDemoAgentIdError(
            scenario,
            SCENARIO_TO_DEMO_ENV_KEY[scenario],
        )
    return str(raw).strip()
