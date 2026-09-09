"""Regression: scenario and MCP modules must import without Settings or a .env."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_IMPORT_SNIPPET = (
    "import eleven_demo.scenarios.telecom, "
    "eleven_demo.scenarios.banking, "
    "eleven_demo.scenarios.healthcare, "
    "eleven_demo.mcp.server"
)

_DROP_ENV = (
    "ELEVENLABS_API_KEY",
    "DEFAULT_AGENT_VOICE_ID",
    "DEFAULT_EN_VOICE_ID",
    "DEFAULT_PT_VOICE_ID",
)


@pytest.mark.slow
def test_scenario_and_mcp_import_without_api_key(tmp_path: Path) -> None:
    env = {k: v for k, v in os.environ.items() if k not in _DROP_ENV}
    result = subprocess.run(
        [sys.executable, "-c", _IMPORT_SNIPPET],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
