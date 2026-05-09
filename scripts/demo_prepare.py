#!/usr/bin/env python3
"""One-shot prep for live demos: verify ElevenLabs auth, provision all agents, write ``.env``.

Run from anywhere after a one-time ``.env`` with ``ELEVENLABS_API_KEY`` and at least one of
``DEFAULT_AGENT_VOICE_ID`` (recommended), ``DEFAULT_EN_VOICE_ID``, or ``DEFAULT_PT_VOICE_ID`` at
the repository root:

    uv run python scripts/demo_prepare.py

Then start the UI:

    uv run python apps/gradio_app.py
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from importlib import import_module
from pathlib import Path

from elevenlabs.core import ApiError

from eleven_demo.client import get_client
from eleven_demo.config import conversational_agent_voice_id, get_settings
from eleven_demo.paths import load_repo_dotenv
from eleven_demo.scenarios.demo_cli import DEMO_SCENARIOS, SCENARIO_TO_DEMO_ENV_KEY


def merge_dotenv_assignments(content: str, updates: dict[str, str]) -> str:
    """Return ``.env`` text with ``updates`` keys replaced in-place or appended.

    Matches lines of the form ``KEY=value`` or optional ``export KEY=value``,
    ignoring leading whitespace on the line.
    """

    pending: dict[str, str] = dict(updates)
    out_lines: list[str] = []
    for raw in content.splitlines(keepends=True):
        line_without_nl = raw.rstrip("\r\n")
        nl = raw[len(line_without_nl) :]
        if not line_without_nl.strip() or line_without_nl.lstrip().startswith("#"):
            out_lines.append(raw)
            continue

        matched: str | None = None
        for key in pending:
            if re.match(rf"^\s*(export\s+)?{re.escape(key)}\s*=", line_without_nl):
                matched = key
                break
        if matched is not None:
            value = pending.pop(matched)
            out_lines.append(f"{matched}={value}{nl or os.linesep}")
        else:
            out_lines.append(raw)

    if pending:
        if out_lines and not out_lines[-1].endswith(("\n", "\r\n")):
            out_lines[-1] = out_lines[-1] + os.linesep
        for key, value in pending.items():
            out_lines.append(f"{key}={value}{os.linesep}")

    return "".join(out_lines)


def _write_dotenv(repo_root: Path, updates: dict[str, str]) -> None:
    env_path = repo_root / ".env"
    previous = env_path.read_text(encoding="utf-8") if env_path.is_file() else ""
    merged = merge_dotenv_assignments(previous, updates)
    env_path.write_text(merged, encoding="utf-8", newline="")


def _smoke_elevenlabs() -> bool:
    try:
        get_client().user.get()
    except ApiError as exc:
        print(f"ElevenLabs auth failed (HTTP {exc.status_code}).", file=sys.stderr)
        return False
    except OSError as exc:
        print(f"ElevenLabs auth failed ({exc}).", file=sys.stderr)
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify API access, provision telecom/banking/healthcare agents, "
            "and persist DEMO_AGENT_ID_* into .env."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Provision and print IDs only; do not modify .env.",
    )
    args = parser.parse_args()

    repo_root = load_repo_dotenv(override=True)
    os.chdir(repo_root)

    get_settings.cache_clear()

    try:
        settings = get_settings()
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        print(
            "Create .env from .env.example and set ELEVENLABS_API_KEY plus a voice id for agents.",
            file=sys.stderr,
        )
        return 1

    if conversational_agent_voice_id(settings) is None:
        print(
            "No agent voice configured. Set DEFAULT_AGENT_VOICE_ID (multilingual), "
            "or DEFAULT_EN_VOICE_ID, or DEFAULT_PT_VOICE_ID in .env (see scripts/voices_pt_br.py).",
            file=sys.stderr,
        )
        return 1

    print("Checking ElevenLabs API key...")
    if not _smoke_elevenlabs():
        return 1
    print("ElevenLabs: OK")

    updates: dict[str, str] = {}
    for scenario in DEMO_SCENARIOS:
        env_key = SCENARIO_TO_DEMO_ENV_KEY[scenario]
        print(f"Provisioning {scenario}...", flush=True)
        module = import_module(f"eleven_demo.scenarios.{scenario}")
        agent_id = module.provision()
        updates[env_key] = agent_id
        print(f"  {env_key}={agent_id}")

    if args.dry_run:
        print("Dry run: .env not modified.")
        return 0

    _write_dotenv(repo_root, updates)
    print(f"Wrote {len(updates)} id(s) to {repo_root / '.env'}")
    print("Next: uv run python apps/gradio_app.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
