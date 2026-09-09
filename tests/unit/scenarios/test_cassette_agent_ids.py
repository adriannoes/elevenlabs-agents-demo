"""Committed scenario cassettes must replay only the English agent URIs."""

from __future__ import annotations

import re
from pathlib import Path

from tests.integration.scenarios._support import _CASSETTE_AGENT_ID, ScenarioName

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CASSETTE_DIR = _REPO_ROOT / "tests" / "integration" / "scenarios" / "cassettes"
_CASSETTE_FILE: dict[ScenarioName, str] = {
    "telecom": "test_telecom_three_turn_regression.yaml",
    "banking": "test_banking_three_turn_regression.yaml",
    "healthcare": "test_healthcare_simulate_first_turn_vcr.yaml",
}
_AGENT_URI = re.compile(
    r"https://api\.elevenlabs\.io/v1/convai/agents/(agent_[0-9a-z]+)/simulate-conversation"
)


def test_scenario_cassettes_only_contain_fallback_agent_uris() -> None:
    """Old PT agent URIs were appended, not replaced; replay must keep one id per file."""

    for scenario, filename in _CASSETTE_FILE.items():
        expected = _CASSETTE_AGENT_ID[scenario]
        text = (_CASSETTE_DIR / filename).read_text(encoding="utf-8")
        found = set(_AGENT_URI.findall(text))
        assert found == {expected}, f"{filename}: expected only {expected}, found {sorted(found)}"
