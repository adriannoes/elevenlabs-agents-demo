#!/usr/bin/env python3
"""CLI: list recent ElevenAgents conversations without running a webhook receiver."""

from __future__ import annotations

import argparse
import json
import re
from typing import Any

from elevenlabs.core import ApiError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from eleven_demo.client import get_client
from eleven_demo.config import get_settings
from eleven_demo.scenarios.demo_cli import (
    DEMO_SCENARIOS,
    MissingDemoAgentIdError,
    require_demo_agent_id,
)

_REDACTION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "[CPF]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"), "[EMAIL]"),
    (re.compile(r"(?<!\+)\b(?:\d[ -]?){13,19}\b"), "[CARD]"),
    (re.compile(r"(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?9?\d{4}[-\s]?\d{4}"), "[PHONE]"),
)


def redact_sensitive_text(value: str) -> str:
    """Redact common Brazilian PII patterns from display text."""
    out = value
    for pattern, replacement in _REDACTION_PATTERNS:
        out = pattern.sub(replacement, out)
    return out


def _resolve_agent_id(scenario: str) -> str:
    try:
        return require_demo_agent_id(get_settings(), scenario)
    except MissingDemoAgentIdError as exc:
        msg = (
            f"Missing {exc.env_key}. Run onboarding and paste the printed id into .env:\n"
            f"  uv run python scripts/agent_create.py {exc.scenario}"
        )
        raise SystemExit(msg) from None


def _safe_text(value: object, *, limit: int = 140) -> str:
    text = "" if value is None else str(value)
    redacted = redact_sensitive_text(text).replace("\n", " ").strip()
    if len(redacted) > limit:
        return f"{redacted[: limit - 1]}…"
    return redacted


def _conversation_attr(item: object, name: str, default: object = "") -> object:
    return getattr(item, name, default)


def _conversation_row_object(item: object) -> dict[str, Any]:
    return {
        "conversation_id": _safe_text(_conversation_attr(item, "conversation_id"), limit=512),
        "agent_name": _safe_text(_conversation_attr(item, "agent_name")),
        "status": _safe_text(_conversation_attr(item, "status")),
        "call_successful": _safe_text(_conversation_attr(item, "call_successful")),
        "call_duration_secs": _conversation_attr(item, "call_duration_secs", None),
        "message_count": _conversation_attr(item, "message_count", None),
        "transcript_summary": _safe_text(_conversation_attr(item, "transcript_summary"), limit=400),
    }


def _conversation_detail_object(detail: object) -> dict[str, Any]:
    analysis = getattr(detail, "analysis", None)
    out: dict[str, Any] = {
        "conversation_id": _safe_text(getattr(detail, "conversation_id", ""), limit=512),
        "agent_name": _safe_text(getattr(detail, "agent_name", "")),
        "status": _safe_text(getattr(detail, "status", "")),
        "analysis": None,
    }
    if analysis is not None:
        out["analysis"] = {
            "call_successful": _safe_text(getattr(analysis, "call_successful", "")),
            "call_summary_title": _safe_text(getattr(analysis, "call_summary_title", "")),
            "transcript_summary": _safe_text(
                getattr(analysis, "transcript_summary", ""),
                limit=2000,
            ),
        }
    return out


def _print_conversation_table(conversations: list[object]) -> None:
    table = Table(title="Recent conversations (redacted summary)")
    table.add_column("conversation_id")
    table.add_column("agent")
    table.add_column("status")
    table.add_column("success")
    table.add_column("duration", justify="right")
    table.add_column("messages", justify="right")
    table.add_column("summary")

    for item in conversations:
        row = _conversation_row_object(item)
        table.add_row(
            str(row["conversation_id"]),
            str(row["agent_name"]),
            str(row["status"]),
            str(row["call_successful"]),
            str(row["call_duration_secs"] if row["call_duration_secs"] is not None else ""),
            str(row["message_count"] if row["message_count"] is not None else ""),
            str(row["transcript_summary"]),
        )
    Console().print(table)


def _print_conversation_detail(detail: object) -> None:
    data = _conversation_detail_object(detail)
    lines = [
        f"[bold]conversation_id[/bold]  {data['conversation_id']}",
        f"[bold]agent[/bold]  {data['agent_name']}",
        f"[bold]status[/bold]  {data['status']}",
    ]
    analysis = data.get("analysis")
    if analysis is not None:
        lines.extend(
            [
                "",
                f"[bold]call_successful[/bold]  {analysis['call_successful']}",
                f"[bold]title[/bold]  {analysis['call_summary_title']}",
                "",
                "[bold]transcript_summary[/bold]",
                analysis["transcript_summary"],
            ]
        )
    Console().print(Panel("\n".join(lines), title="Conversation detail", expand=False))


def main() -> None:
    """Run the conversations CLI."""
    parser = argparse.ArgumentParser(
        description="List or inspect recent ElevenAgents conversations with redacted output.",
    )
    parser.add_argument("scenario", nargs="?", choices=DEMO_SCENARIOS, help="Demo scenario")
    parser.add_argument("--id", dest="conversation_id", help="Fetch one conversation by id")
    parser.add_argument("--page-size", type=int, default=10, help="Number of conversations to list")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON on stdout (redacted fields).",
    )
    args = parser.parse_args()

    conversations = get_client().conversational_ai.conversations
    try:
        if args.conversation_id:
            detail = conversations.get(conversation_id=args.conversation_id)
            if args.json:
                print(json.dumps(_conversation_detail_object(detail), indent=2, ensure_ascii=False))
            else:
                _print_conversation_detail(detail)
            return

        if args.scenario is None:
            msg = "Pass a scenario (telecom|banking|healthcare) or --id <conversation_id>."
            raise SystemExit(msg)

        agent_id = _resolve_agent_id(args.scenario)
        page = conversations.list(agent_id=agent_id, page_size=args.page_size)
        items = list(getattr(page, "conversations", []))
        if args.json:
            payload = {"conversations": [_conversation_row_object(item) for item in items]}
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            _print_conversation_table(items)
    except ApiError as exc:
        msg = f"Conversations API failed: {exc.status_code} {exc.body}"
        raise SystemExit(msg) from exc


if __name__ == "__main__":
    main()
