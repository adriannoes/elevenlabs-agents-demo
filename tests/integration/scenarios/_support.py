"""Shared helpers for scenario simulate integration tests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import pytest

from eleven_demo.agents import SimulationResult, simulate
from eleven_demo.config import Settings, get_settings

if TYPE_CHECKING:
    from pytest import FixtureRequest

ScenarioName = Literal["telecom", "banking", "healthcare"]

_AGENT_ATTR: dict[ScenarioName, str] = {
    "telecom": "demo_agent_id_telecom",
    "banking": "demo_agent_id_banking",
    "healthcare": "demo_agent_id_healthcare",
}

_ENV_HINT: dict[ScenarioName, str] = {
    "telecom": "DEMO_AGENT_ID_TELECOM",
    "banking": "DEMO_AGENT_ID_BANKING",
    "healthcare": "DEMO_AGENT_ID_HEALTHCARE",
}

# URI segment in committed VCR cassettes (`simulate-conversation` path). Replay must send
# the same URL the fixture recorded; unset env falls back here when the cassette is on disk.
_CASSETTE_AGENT_ID: dict[ScenarioName, str] = {
    "telecom": "agent_6801kqv0a5defk3841wy15q56cv6",
    "banking": "agent_6701kqv0a71cevms7t4hbg9gz6a5",
    "healthcare": "agent_7501kqv0aadyfx7spc2r93djw1bb",
}


def scenario_cassette_path(request: FixtureRequest) -> Path:
    """Path to the pytest-vcr YAML cassette for a top-level test function."""

    test_dir = Path(request.node.path).parent
    return test_dir / "cassettes" / f"{request.node.name}.yaml"


def skip_scenario_simulate_unless_runnable(
    request: FixtureRequest,
    scenario: ScenarioName,
) -> None:
    """Skip with guidance when neither a cassette nor live credentials are available.

    Live recording requires ``ELEVENLABS_API_KEY`` and the matching ``DEMO_AGENT_ID_*``
    from provisioning (see ``scripts/agent_create.py``). ``simulate`` does not use
    ``DEFAULT_PT_VOICE_ID``; that check was removed to avoid pointless skips.
    Replay still needs a non-empty ``ELEVENLABS_API_KEY`` in the environment so
    :func:`~eleven_demo.config.get_settings` can build the SDK client (CI may use a
    placeholder key when only replaying sanitized cassettes).
    """

    cassette = scenario_cassette_path(request)
    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if cassette.is_file():
        if not api_key:
            pytest.skip(
                "VCR replay still loads Settings; set ELEVENLABS_API_KEY (placeholder ok locally) "
                f"or add a key in CI. Cassette: {cassette.as_posix()}",
            )
        return

    if not api_key:
        pytest.skip(
            "Set ELEVENLABS_API_KEY to record this cassette, or commit a sanitized cassette at "
            f"{cassette.as_posix()}",
        )

    raw_agent = getattr(get_settings(), _AGENT_ATTR[scenario])
    if raw_agent is None or not str(raw_agent).strip():
        env = _ENV_HINT[scenario]
        pytest.skip(
            f"Record once with a provisioned agent: set {env} (output of "
            f"`uv run python scripts/agent_create.py {scenario}`).",
        )


def resolve_agent_id(
    settings: Settings,
    scenario: ScenarioName,
    *,
    cassette_path: Path | None = None,
) -> str:
    """Return the demo agent id for ``scenario`` or raise if missing."""

    raw = getattr(settings, _AGENT_ATTR[scenario])
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    if cassette_path is not None and cassette_path.is_file():
        return _CASSETTE_AGENT_ID[scenario]
    msg = f"Missing {_ENV_HINT[scenario]}"
    raise ValueError(msg)


def run_three_turn(
    scenario: ScenarioName,
    messages: list[str],
    *,
    language: str = "en",
    cassette_path: Path | None = None,
) -> SimulationResult:
    """Run :func:`~eleven_demo.agents.simulate` with three user lines for the scenario."""

    settings = get_settings()
    agent_id = resolve_agent_id(settings, scenario, cassette_path=cassette_path)
    return simulate(agent_id, messages, language=language)


def assert_simulation_shape(result: SimulationResult) -> None:
    """Assert stable structure from :class:`~eleven_demo.agents.SimulationResult`."""

    assert result.transcript, "expected non-empty transcript"
    assert result.analysis.call_successful, "expected analysis.call_successful"
    assert result.analysis.transcript_summary.strip(), "expected analysis.transcript_summary"


def tool_call_names(result: SimulationResult) -> set[str]:
    """Set of tool names invoked across the merged simulation."""

    return {tc.tool_name for tc in result.tool_calls}
