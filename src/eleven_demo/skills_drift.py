"""Compare upstream ``elevenlabs/skills`` copy against canonical Models docs.

Used by ``scripts/skills_model_drift.py``. Network is optional: pass markdown
strings in tests; the CLI fetches live pages.

These checks are **line-level regex heuristics**, not table parsers: they look for
model IDs with word boundaries, deprecation notes on the same row, and the first
``up to N terms`` phrase near the word ``keyterm``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

import httpx

DEFAULT_MODELS_URL = "https://elevenlabs.io/docs/overview/models.md"
DEFAULT_TTS_SKILL_URL = (
    "https://raw.githubusercontent.com/elevenlabs/skills/main/text-to-speech/SKILL.md"
)
DEFAULT_STT_SKILL_URL = (
    "https://raw.githubusercontent.com/elevenlabs/skills/main/speech-to-text/SKILL.md"
)

TURBO_REPLACEMENTS: dict[str, str] = {
    "eleven_turbo_v2_5": "eleven_flash_v2_5",
    "eleven_turbo_v2": "eleven_flash_v2",
}

USER_AGENT = "eleven-demo-skills-drift/0.1 (+https://github.com/adriannoes/elevenlabs-agents-demo)"

_MODEL_ID_PATTERN_TEMPLATE = r"`?{id}`?(?!\w)"
_KEYTERM_CAP_PATTERN = re.compile(r"up to\s+(\d+)\s+terms", flags=re.IGNORECASE)
_KEYTERM_WINDOW_LINES = 10


class DocsFetchError(RuntimeError):
    """Raised when a docs URL returns a soft-404 or otherwise unusable body."""


@dataclass(frozen=True, slots=True)
class DriftFinding:
    """One mismatch between a skill page and canonical docs."""

    skill: Literal["text-to-speech", "speech-to-text"]
    code: str
    summary: str
    skill_evidence: str
    docs_evidence: str


def _model_id_pattern(model_id: str) -> re.Pattern[str]:
    return re.compile(_MODEL_ID_PATTERN_TEMPLATE.format(id=re.escape(model_id)))


def _lines_mentioning_model_id(haystack: str, model_id: str) -> list[str]:
    """Return stripped lines that mention ``model_id`` as a whole token.

    ``eleven_turbo_v2`` must not match a line that only contains ``eleven_turbo_v2_5``.
    """

    pattern = _model_id_pattern(model_id)
    return [ln.strip() for ln in haystack.splitlines() if pattern.search(ln)]


def fetch_text(
    url: str,
    *,
    timeout_s: float = 30.0,
    client: httpx.Client | None = None,
) -> str:
    """GET a URL and return response text.

    Raises:
        httpx.HTTPError: on non-2xx or transport failure.
        DocsFetchError: when the body is an elevenlabs.io soft-404
            (HTTP 200 whose first heading is ``# Page Not Found``).

    Args:
        url: Absolute URL to fetch.
        timeout_s: Request timeout in seconds.
        client: Optional injected ``httpx.Client`` (tests use ``MockTransport``).
            When omitted, a short-lived client is created and closed.

    Example:
        ``fetch_text(DEFAULT_MODELS_URL)`` returns the Models markdown page.
    """

    owns_client = client is None
    http = client or httpx.Client()
    try:
        response = http.get(
            url,
            timeout=timeout_s,
            headers={"User-Agent": USER_AGENT, "Accept": "text/plain, text/markdown, */*"},
            follow_redirects=True,
        )
        response.raise_for_status()
        text = response.text
        first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
        if first_line == "# Page Not Found":
            msg = f"soft-404 from {url}: {first_line}"
            raise DocsFetchError(msg)
        return text
    finally:
        if owns_client:
            http.close()


def tts_turbo_listed_without_deprecation(skill_md: str, models_md: str) -> list[DriftFinding]:
    """Turbo IDs on a skill row with no same-line deprecation note, while Models deprecates them.

    The Models-side check is: a ``Deprecated models`` heading exists **and** the turbo
    id appears as a bounded token somewhere on that page. There is no DOTALL fallback
    that would treat any later ``flash`` mention as evidence of deprecation.
    """

    findings: list[DriftFinding] = []
    models_lower = models_md.lower()
    docs_has_deprecated_heading = "deprecated models" in models_lower
    for turbo_id, flash_id in TURBO_REPLACEMENTS.items():
        skill_lines = _lines_mentioning_model_id(skill_md, turbo_id)
        if not skill_lines:
            continue
        skill_has_deprecation = any("deprecat" in ln.lower() for ln in skill_lines)
        docs_says_deprecated = docs_has_deprecated_heading and bool(
            _lines_mentioning_model_id(models_md, turbo_id)
        )
        if docs_says_deprecated and not skill_has_deprecation:
            findings.append(
                DriftFinding(
                    skill="text-to-speech",
                    code="turbo_not_marked_deprecated",
                    summary=(
                        f"`{turbo_id}` appears in the TTS skill models table without a "
                        f"deprecation note; canonical Models recommends `{flash_id}`."
                    ),
                    skill_evidence=skill_lines[0][:240],
                    docs_evidence=(
                        f"Models page documents `{turbo_id}` as deprecated; use `{flash_id}`."
                    ),
                )
            )
    return findings


def _keyterm_cap(md: str) -> int | None:
    """First ``up to N terms`` whose own line or previous 10 lines mention ``keyterm``."""

    lines = md.splitlines()
    for match in _KEYTERM_CAP_PATTERN.finditer(md):
        line_idx = md[: match.start()].count("\n")
        window_start = max(0, line_idx - _KEYTERM_WINDOW_LINES)
        window = "\n".join(lines[window_start : line_idx + 1])
        if "keyterm" in window.lower():
            return int(match.group(1))
    return None


def stt_keyterm_cap_mismatch(skill_md: str, models_md: str) -> list[DriftFinding]:
    """Keyterm prompting cap: first keyterm-anchored ``up to N terms`` on each page."""

    skill_n = _keyterm_cap(skill_md)
    docs_n = _keyterm_cap(models_md)
    if skill_n is None or docs_n is None:
        return []
    if skill_n == docs_n:
        return []
    return [
        DriftFinding(
            skill="speech-to-text",
            code="keyterm_cap_mismatch",
            summary=(f"Scribe keyterm cap is {skill_n} in the STT skill and {docs_n} on Models."),
            skill_evidence=f"up to {skill_n} terms",
            docs_evidence=f"up to {docs_n} terms",
        )
    ]


def collect_findings(
    *,
    tts_skill_md: str,
    stt_skill_md: str,
    models_md: str,
) -> list[DriftFinding]:
    """Run the lab's drift heuristics on already-fetched markdown."""

    return [
        *tts_turbo_listed_without_deprecation(tts_skill_md, models_md),
        *stt_keyterm_cap_mismatch(skill_md=stt_skill_md, models_md=models_md),
    ]
