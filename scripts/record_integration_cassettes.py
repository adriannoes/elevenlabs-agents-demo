#!/usr/bin/env python3
"""Record pytest-vcr cassettes for integration tests (live API = billable credits).

Prerequisites:
    - ``ELEVENLABS_API_KEY`` and ``DEFAULT_PT_VOICE_ID`` (this script's integration targets still
      assume the PT default voice path for TTS/vendor legs)
    - ``OPENAI_API_KEY`` for the vendor benchmark integration cassette
    - ``DEMO_AGENT_ID_*`` for each scenario, or pass ``--provision`` to upsert agents
      via ``scripts/agent_create.py`` (idempotent; upsert uses any configured agent voice per
      ``eleven_demo.config.resolve_conversational_agent_voice_id``)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from eleven_demo.paths import load_repo_dotenv
from eleven_demo.scenarios.demo_cli import DEMO_SCENARIOS, SCENARIO_TO_DEMO_ENV_KEY


def _ensure_env(name: str) -> str:
    value = (os.environ.get(name) or "").strip()
    if not value:
        msg = f"Missing {name} in the environment (set in .env or export)."
        raise SystemExit(msg)
    return value


def _provision_agent(repo_root: Path, scenario: str) -> str:
    proc = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "agent_create.py"), scenario],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or proc.stdout or f"agent_create {scenario} failed\n")
        raise SystemExit(proc.returncode)
    lines = [ln.strip() for ln in proc.stdout.strip().splitlines() if ln.strip()]
    if not lines:
        msg = f"agent_create {scenario} produced no stdout"
        raise SystemExit(msg)
    return lines[-1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provision",
        action="store_true",
        help="Upsert telecom/banking/healthcare agents when DEMO_AGENT_ID_* unset.",
    )
    args = parser.parse_args()

    repo_root = load_repo_dotenv()

    _ensure_env("ELEVENLABS_API_KEY")
    _ensure_env("DEFAULT_PT_VOICE_ID")
    _ensure_env("OPENAI_API_KEY")

    agent_envs = [(s, SCENARIO_TO_DEMO_ENV_KEY[s]) for s in DEMO_SCENARIOS]
    if args.provision:
        for scenario, env_name in agent_envs:
            if (os.environ.get(env_name) or "").strip():
                print(f"{env_name} already set, skipping {scenario} provision")
                continue
            print(f"Provisioning {scenario} → {env_name} …")
            agent_id = _provision_agent(repo_root, scenario)
            os.environ[env_name] = agent_id
            print(f"  exported for this process ({env_name})")

    for _, env_name in agent_envs:
        _ensure_env(env_name)

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/integration/scenarios",
        "tests/integration/benchmarks/test_vendor_benchmark_integration.py",
        "-m",
        "integration",
        "-v",
        "--tb=short",
        "--vcr-record=all",
    ]
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=repo_root, check=False)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
