"""Integration: Healthcare scenario — simulate round-one regression (VCR)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.scenarios._support import (
    assert_simulation_shape,
    run_three_turn,
    scenario_cassette_path,
    skip_scenario_simulate_unless_runnable,
)

if TYPE_CHECKING:
    from pytest import FixtureRequest

# First scripted user utterance matches the sanitized cassette (`record_mode='once'`).
# Re-record multi-turn simulate flows if you extend this test; merged cassettes can pair
# the wrong responses to middle turns and break deterministic replay.
_HEALTHCARE_FIRST_TURN_TRIAGE: list[str] = [
    "Estou com febre alta há dois dias e cansaço.",
]

_TRIAGE_AGENT_SUBSTRINGS: frozenset[str] = frozenset(("triagem", "orient", "triage"))


@pytest.mark.integration
@pytest.mark.vcr(
    filter_headers=["xi-api-key", "authorization"],
    record_mode="once",
    match_on=["method", "scheme", "host", "port", "path", "body"],
)
def test_healthcare_simulate_first_turn_vcr(request: FixtureRequest) -> None:
    """Stable simulate smoke: greeting + scripted triage language (cassette-backed)."""

    skip_scenario_simulate_unless_runnable(request, "healthcare")
    cassette = scenario_cassette_path(request)
    result = run_three_turn(
        "healthcare",
        _HEALTHCARE_FIRST_TURN_TRIAGE,
        language="en",
        cassette_path=cassette,
    )
    assert_simulation_shape(result)
    agent_text = " ".join((t.message or "").lower() for t in result.transcript if t.role == "agent")
    assert any(s in agent_text for s in _TRIAGE_AGENT_SUBSTRINGS), (
        "expected triage-orientation wording in agent turns matching the committed cassette"
    )
