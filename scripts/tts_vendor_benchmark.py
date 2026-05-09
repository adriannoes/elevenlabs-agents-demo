#!/usr/bin/env python3
"""CLI: compare ElevenLabs vs OpenAI streaming TTS (TTFB-focused)."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from rich.console import Console
from rich.table import Table

from eleven_demo.benchmarks.tts_vendor import (
    VENDOR_CANONICAL_TEXT_SETS,
    benchmark_report_to_serializable,
    run_vendor_benchmark,
)
from eleven_demo.config import get_settings

_EPILOG = """examples:
  %(prog)s --n 5 --text-set short-pt-br --out artifacts/benchmarks/run.json
  %(prog)s --n 1 --openai-format pcm --quiet

Requires DEFAULT_PT_VOICE_ID and OPENAI_API_KEY in the environment (.env).
"""

TEXT_SETS: dict[str, tuple[str, ...]] = dict(VENDOR_CANONICAL_TEXT_SETS)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ElevenLabs vs OpenAI TTS vendor benchmark.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_EPILOG,
    )
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--text-set", default="short-pt-br", choices=sorted(TEXT_SETS.keys()))
    parser.add_argument("--eleven-model", default=None)
    parser.add_argument("--openai-model", default=None)
    parser.add_argument("--openai-format", default=None, choices=["mp3", "pcm"])
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Write JSON only; skip the Rich summary table and path message.",
    )
    parser.add_argument(
        "--out",
        default="artifacts/benchmarks/tts-vendor-latest.json",
        help="JSON report path",
    )
    args = parser.parse_args()

    settings = get_settings()
    err = Console(stderr=True)
    if settings.openai_api_key is None or not settings.openai_api_key.get_secret_value().strip():
        err.print(
            "[yellow]Vendor benchmark needs OPENAI_API_KEY in the environment. "
            "Set it in .env (see .env.example) or export it before running.[/yellow]"
        )
        raise SystemExit(2)

    if not settings.default_pt_voice_id:
        err.print(
            "[yellow]Set DEFAULT_PT_VOICE_ID for the ElevenLabs leg "
            "(e.g. pick one from scripts/voices_pt_br.py).[/yellow]"
        )
        raise SystemExit(2)

    texts = list(TEXT_SETS[args.text_set])
    report = run_vendor_benchmark(
        texts,
        args.n,
        eleven_model_id=args.eleven_model,
        openai_model_id=args.openai_model,
        openai_response_format=args.openai_format,
    )

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    payload = benchmark_report_to_serializable(report)
    outp.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.quiet:
        return

    table = Table(title="Vendor TTS summary (TTFB ms)")
    table.add_column("provider")
    table.add_column("median_ttfb", justify="right")
    table.add_column("p95_ttfb", justify="right")
    table.add_column("mean_ttfb", justify="right")
    table.add_column("median_total_ms", justify="right")
    table.add_column("n", justify="right")

    for s in report.summaries:
        if math.isnan(s.median_ttfb_ms):
            table.add_row(s.provider, "n/a", "n/a", "n/a", "n/a", str(s.sample_count))
        else:
            table.add_row(
                s.provider,
                f"{s.median_ttfb_ms:.1f}",
                f"{s.p95_ttfb_ms:.1f}",
                f"{s.mean_ttfb_ms:.1f}",
                f"{s.median_total_ms:.1f}",
                str(s.sample_count),
            )

    console = Console()
    console.print(table)
    console.print(f"Wrote [bold]{outp.resolve()}[/bold]")


if __name__ == "__main__":
    main()
