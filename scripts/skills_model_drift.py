#!/usr/bin/env python3
"""Fetch live ElevenLabs docs + skills and print model-ID drift."""

from __future__ import annotations

import argparse
import json

import httpx
from rich.console import Console
from rich.table import Table

from eleven_demo.skills_drift import (
    DEFAULT_MODELS_URL,
    DEFAULT_STT_SKILL_URL,
    DEFAULT_TTS_SKILL_URL,
    DocsFetchError,
    collect_findings,
    fetch_text,
)


def main() -> None:
    """Fetch Models + skill markdown and exit 1 when heuristics report drift.

    Exit codes: 0 (no findings), 1 (drift), 2 (fetch failed).
    """

    parser = argparse.ArgumentParser(
        description=(
            "Compare elevenlabs/skills model tables against /docs/overview/models. "
            "Exit 1 when drift is found."
        )
    )
    parser.add_argument("--models-url", default=DEFAULT_MODELS_URL)
    parser.add_argument("--tts-skill-url", default=DEFAULT_TTS_SKILL_URL)
    parser.add_argument("--stt-skill-url", default=DEFAULT_STT_SKILL_URL)
    parser.add_argument("--json", action="store_true", help="Print findings as JSON.")
    args = parser.parse_args()

    console = Console()
    try:
        models_md = fetch_text(args.models_url)
        tts_md = fetch_text(args.tts_skill_url)
        stt_md = fetch_text(args.stt_skill_url)
    except (httpx.HTTPError, httpx.InvalidURL, DocsFetchError) as exc:
        console.print(f"[red]fetch failed:[/red] {exc}")
        raise SystemExit(2) from exc

    findings = collect_findings(tts_skill_md=tts_md, stt_skill_md=stt_md, models_md=models_md)
    if args.json:
        payload = [
            {
                "skill": f.skill,
                "code": f.code,
                "summary": f.summary,
                "skill_evidence": f.skill_evidence,
                "docs_evidence": f.docs_evidence,
            }
            for f in findings
        ]
        console.print_json(json.dumps(payload))
    elif not findings:
        console.print(
            "[green]No drift findings[/green] (lab checks: Turbo deprecation, STT keyterm cap)."
        )
    else:
        table = Table(title="elevenlabs/skills vs Models")
        table.add_column("Skill")
        table.add_column("Code")
        table.add_column("Summary")
        for f in findings:
            table.add_row(f.skill, f.code, f.summary)
        console.print(table)
        console.print("\nMethodology: docs/upstream-skills-notes.md")

    raise SystemExit(1 if findings else 0)


if __name__ == "__main__":
    main()
