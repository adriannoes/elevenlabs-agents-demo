#!/usr/bin/env python3
"""Start ws_bridge, Next.js, and optionally Gradio for a unified local demo."""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request

from eleven_demo.paths import repo_root

REPO_ROOT = repo_root()

PROCS: list[subprocess.Popen[bytes]] = []


def _uv_prefixed(*tail: str) -> list[str]:
    uv_bin = shutil.which("uv")
    if uv_bin is None:
        msg = "`uv` is not installed or not on PATH."
        raise RuntimeError(msg)
    return [uv_bin, "run", *tail]


def _wait_health(url: str, *, deadline_sec: float) -> None:
    deadline = time.monotonic() + deadline_sec
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:  # noqa: S310 — local health
                if resp.getcode() == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.25)
    msg = f"Timed out waiting for health check: {url}"
    raise TimeoutError(msg)


def terminate_children() -> None:
    """Stop child processes roughly in reverse start order."""
    for proc in reversed(PROCS):
        if proc.poll() is None:
            proc.send_signal(signal.SIGTERM)


def exit_handler(*_: object) -> None:
    terminate_children()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run FastAPI Convai tools bridge plus Next.js and optional Gradio.",
    )
    parser.add_argument(
        "--bridge-port",
        type=int,
        default=8788,
        help="TCP port for apps/ws_bridge (default: 8788).",
    )
    parser.add_argument(
        "--next-port",
        type=int,
        default=3000,
        help="TCP port for Next.js (default: 3000).",
    )
    parser.add_argument(
        "--web",
        choices=("dev", "prod"),
        default="prod",
        help=(
            "`dev`: next dev. "
            "`prod`: next build + next start (default; matches npm run build on demo day)."
        ),
    )
    parser.add_argument(
        "--no-gradio",
        action="store_true",
        help="Skip Gradio (multi-vertical playground).",
    )
    parser.add_argument(
        "--health-timeout",
        type=float,
        default=45.0,
        help="Seconds to wait for ws_bridge /healthz (default: 45).",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help=("With `--web prod`, reuse an existing `.next` build (skips `pnpm run build`)."),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if shutil.which("pnpm") is None:
        msg = "`pnpm` is not installed or not on PATH."
        raise RuntimeError(msg)

    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)

    bridge_cmd = _uv_prefixed(
        "uvicorn",
        "apps.ws_bridge.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(args.bridge_port),
    )
    proc_bridge = subprocess.Popen(bridge_cmd, cwd=str(REPO_ROOT))
    PROCS.append(proc_bridge)

    health = f"http://127.0.0.1:{args.bridge_port}/healthz"

    env = dict(os.environ)
    env["INTERNAL_WS_BRIDGE_TOOLS_URL"] = f"http://127.0.0.1:{args.bridge_port}/convai/demo-tools"

    try:
        _wait_health(health, deadline_sec=args.health_timeout)
    except TimeoutError:
        terminate_children()
        sys.stderr.write(f"Timed out: ws_bridge did not respond at {health}. Check logs above.\n")
        raise SystemExit(1) from None

    if not args.no_gradio:
        proc_ui = subprocess.Popen(
            _uv_prefixed("python", "apps/gradio_app.py"),
            cwd=str(REPO_ROOT),
            env=dict(env),
        )
        PROCS.append(proc_ui)

    env_for_next = {**env, "PORT": str(args.next_port)}

    if args.web == "prod":
        if not args.skip_build:
            subprocess.run(
                ["pnpm", "--dir", "apps/web", "run", "build"],
                cwd=str(REPO_ROOT),
                env=dict(env_for_next),
                check=True,
            )
        proc_next = subprocess.Popen(
            ["pnpm", "--dir", "apps/web", "run", "start"],
            cwd=str(REPO_ROOT),
            env=dict(env_for_next),
        )
    else:
        proc_next = subprocess.Popen(
            ["pnpm", "--dir", "apps/web", "run", "dev"],
            cwd=str(REPO_ROOT),
            env=dict(env_for_next),
        )

    PROCS.append(proc_next)

    tunnel_note = (
        "Expose port "
        f"{args.next_port} over HTTPS so ElevenLabs can reach tools via Next; "
        "then set in repo `.env`:"
        "\n"
        "  CONVAI_DEMO_TOOL_WEBHOOK_URL=https://<public-host>/api/convai/demo-tools"
        "\n"
        "Re-run: uv run python scripts/agent_create.py telecom"
        "\n"
        "(provision again whenever the tunnel hostname changes)."
    )

    banner = (
        "\nDemo stack running:\n"
        f"- Convai tools (direct): http://127.0.0.1:{args.bridge_port}/convai/demo-tools\n"
        f"- Next.js:               http://127.0.0.1:{args.next_port}/\n"
    )
    if not args.no_gradio:
        banner += "- Gradio:                http://127.0.0.1:7860/\n"
    banner += "\n" + tunnel_note + "\n"

    sys.stdout.write(banner)
    sys.stdout.flush()

    try:
        exit_code = proc_next.wait()
    finally:
        terminate_children()
    sys.exit(exit_code if isinstance(exit_code, int) else 1)


if __name__ == "__main__":
    main()
