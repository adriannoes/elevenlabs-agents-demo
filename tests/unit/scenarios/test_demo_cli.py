"""Tests for demo CLI scenario maps."""

from __future__ import annotations

from pathlib import Path

import pytest

from eleven_demo.config import Settings
from eleven_demo.scenarios.demo_cli import (
    DEMO_SCENARIOS,
    SCENARIO_TO_DEMO_ENV_KEY,
    SCENARIO_TO_SETTINGS_FIELD,
    MissingDemoAgentIdError,
    require_demo_agent_id,
)


def test_scenario_maps_are_consistent() -> None:
    assert set(DEMO_SCENARIOS) == set(SCENARIO_TO_SETTINGS_FIELD) == set(SCENARIO_TO_DEMO_ENV_KEY)


def test_require_demo_agent_id_raises_when_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "x" * 32)
    monkeypatch.delenv("DEMO_AGENT_ID_TELECOM", raising=False)
    settings = Settings()
    with pytest.raises(MissingDemoAgentIdError) as exc_info:
        require_demo_agent_id(settings, "telecom")
    assert exc_info.value.env_key == "DEMO_AGENT_ID_TELECOM"
    assert exc_info.value.scenario == "telecom"


def test_require_demo_agent_id_returns_stripped(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "x" * 32)
    monkeypatch.setenv("DEMO_AGENT_ID_TELECOM", "  ag_123  ")
    settings = Settings()
    assert require_demo_agent_id(settings, "telecom") == "ag_123"
