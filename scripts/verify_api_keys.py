#!/usr/bin/env python3
"""Smoke-check API keys from `.env` without printing secrets.

Run from the repository root so pydantic-settings can load `.env`:

    uv run python scripts/verify_api_keys.py

ElevenLabs: calls ``GET /v1/user`` via the SDK. OpenAI: calls ``GET /v1/models`` over HTTPS.
"""

from __future__ import annotations

import os
import sys

import httpx
from elevenlabs.core import ApiError
from pydantic import ValidationError

from eleven_demo.client import get_client
from eleven_demo.paths import load_repo_dotenv


def _load_env() -> None:
    load_repo_dotenv()


def check_elevenlabs() -> bool:
    """Return True if the configured ElevenLabs key authenticates."""

    try:
        get_client().user.get()
    except ValidationError:
        print("  ElevenLabs: FAILED (ELEVENLABS_API_KEY missing or empty in .env)")
        return False
    except ApiError as exc:
        print(f"  ElevenLabs: FAILED (ApiError HTTP {exc.status_code})")
        return False
    except OSError as exc:
        print(f"  ElevenLabs: FAILED ({exc!s})")
        return False
    print("  ElevenLabs: OK")
    return True


def check_openai() -> bool | None:
    """Return True if OpenAI key works, False on auth failure, None if unset."""

    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        print("  OpenAI: SKIP (OPENAI_API_KEY unset)")
        return None

    try:
        response = httpx.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=30.0,
        )
    except httpx.HTTPError as exc:
        print(f"  OpenAI: FAILED ({exc!s})")
        return False

    if response.status_code == 200:
        print("  OpenAI: OK")
        return True

    print(f"  OpenAI: FAILED (HTTP {response.status_code})")
    return False


def main() -> int:
    _load_env()
    print("API key smoke check (no secrets printed):")
    el_ok = check_elevenlabs()
    oa = check_openai()

    if oa is None:
        return 0 if el_ok else 1
    return 0 if el_ok and oa else 1


if __name__ == "__main__":
    sys.exit(main())
