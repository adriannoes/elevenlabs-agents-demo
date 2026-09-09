"""Unit tests for skills vs Models drift checks (no network)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest
from scripts import skills_model_drift

from eleven_demo.skills_drift import (
    DocsFetchError,
    collect_findings,
    fetch_text,
    stt_keyterm_cap_mismatch,
    tts_turbo_listed_without_deprecation,
)

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch

TTS_SKILL_WITH_TURBO = """
## Models

| Model ID | Languages | Latency | Best For |
|----------|-----------|---------|----------|
| `eleven_flash_v2_5` | 32 | ~75ms | Ultra-low latency |
| `eleven_turbo_v2_5` | 32 | ~250-300ms | Balanced quality/speed |
| `eleven_turbo_v2` | English | ~250-300ms | English-only, balanced |
"""

TTS_SKILL_FLASH_ONLY = """
## Models

| Model ID | Languages | Latency |
|----------|-----------|---------|
| `eleven_flash_v2_5` | 32 | ~75ms |
"""

TTS_SKILL_ONLY_V2_5 = """
## Models

| Model ID | Languages | Latency |
|----------|-----------|---------|
| `eleven_turbo_v2_5` | 32 | ~250-300ms |
"""

TTS_SKILL_V2_5_ANNOTATED = """
## Models

| Model ID | Languages | Latency | Notes |
|----------|-----------|---------|-------|
| `eleven_turbo_v2_5` | 32 | ~250-300ms | deprecated, prefer Flash |
| `eleven_turbo_v2` | English | ~250-300ms | English-only, balanced |
"""

TTS_SKILL_STRAY_DEPRECATED_HEADING = (
    TTS_SKILL_WITH_TURBO + "\n\nSee Deprecated models in the canonical docs.\n"
)

MODELS_WITH_DEPRECATED_TURBO = """
## Flagship models

`eleven_flash_v2_5` Ultra-fast

### Deprecated models

The `eleven_turbo_v2_5` and `eleven_turbo_v2` models are functionally equivalent to the
`eleven_flash_v2_5` and `eleven_flash_v2` models respectively, except the latency on the Flash
models is lower on average. We recommend using the Flash models over Turbo models in all use
cases.
"""

MODELS_FLASH_AFTER_TURBO_NO_DEPRECATION = """
Use `eleven_turbo_v2_5` for low latency.

Also `eleven_flash_v2_5` exists.
"""

STT_SKILL_100 = "Help the model recognize specific words (up to 100 terms):"
MODELS_1000 = "Keyterm prompting, up to 1000 terms"


def test_turbo_drift_when_skill_omits_deprecation() -> None:
    findings = tts_turbo_listed_without_deprecation(
        TTS_SKILL_WITH_TURBO, MODELS_WITH_DEPRECATED_TURBO
    )
    codes = {f.code for f in findings}
    assert codes == {"turbo_not_marked_deprecated"}
    ids = " ".join(f.summary for f in findings)
    assert "eleven_turbo_v2_5" in ids
    assert "eleven_turbo_v2" in ids
    v2 = next(f for f in findings if "eleven_turbo_v2`" in f.summary)
    assert "eleven_turbo_v2_5" not in v2.skill_evidence
    assert "eleven_turbo_v2" in v2.skill_evidence


def test_no_turbo_drift_when_skill_has_no_turbo_rows() -> None:
    findings = tts_turbo_listed_without_deprecation(
        TTS_SKILL_FLASH_ONLY, MODELS_WITH_DEPRECATED_TURBO
    )
    assert findings == []


def test_flash_after_turbo_without_deprecated_heading_is_not_drift() -> None:
    findings = tts_turbo_listed_without_deprecation(
        TTS_SKILL_WITH_TURBO, MODELS_FLASH_AFTER_TURBO_NO_DEPRECATION
    )
    assert findings == []


def test_v2_5_row_does_not_count_as_v2_evidence() -> None:
    findings = tts_turbo_listed_without_deprecation(
        TTS_SKILL_ONLY_V2_5, MODELS_WITH_DEPRECATED_TURBO
    )
    assert len(findings) == 1
    assert "eleven_turbo_v2_5" in findings[0].summary
    assert "eleven_turbo_v2_5" in findings[0].skill_evidence
    assert "eleven_turbo_v2`" not in findings[0].summary.replace("eleven_turbo_v2_5", "")


def test_annotating_only_v2_5_row_leaves_v2_finding() -> None:
    findings = tts_turbo_listed_without_deprecation(
        TTS_SKILL_V2_5_ANNOTATED, MODELS_WITH_DEPRECATED_TURBO
    )
    assert len(findings) == 1
    assert "eleven_turbo_v2`" in findings[0].summary
    assert "eleven_turbo_v2_5" not in findings[0].skill_evidence
    assert (
        "`eleven_turbo_v2`" in findings[0].skill_evidence
        or "eleven_turbo_v2 |" in findings[0].skill_evidence
    )


def test_stray_deprecated_models_phrase_does_not_suppress_rows() -> None:
    findings = tts_turbo_listed_without_deprecation(
        TTS_SKILL_STRAY_DEPRECATED_HEADING, MODELS_WITH_DEPRECATED_TURBO
    )
    assert {f.code for f in findings} == {"turbo_not_marked_deprecated"}
    assert len(findings) == 2


def test_keyterm_and_turbo_collected() -> None:
    findings = collect_findings(
        tts_skill_md=TTS_SKILL_WITH_TURBO,
        stt_skill_md="## Keyterm Prompting\n" + STT_SKILL_100,
        models_md=MODELS_WITH_DEPRECATED_TURBO + "\n" + MODELS_1000,
    )
    assert any(f.code == "keyterm_cap_mismatch" for f in findings)
    assert any(f.code == "turbo_not_marked_deprecated" for f in findings)


def test_matching_keyterm_caps_are_silent() -> None:
    findings = collect_findings(
        tts_skill_md=TTS_SKILL_FLASH_ONLY,
        stt_skill_md="Keyterm prompting, up to 1000 terms",
        models_md=MODELS_WITH_DEPRECATED_TURBO + "\nKeyterm prompting, up to 1000 terms",
    )
    assert findings == []


def test_keyterm_ignores_earlier_non_keyterm_up_to_n_terms() -> None:
    skill = (
        "Speaker diarization, up to 32 speakers\n"
        "Glossary size, up to 5 terms of art.\n"
        "## Keyterm Prompting\n"
        "Help the model recognize specific words (up to 100 terms):\n"
    )
    models = "Speaker diarization, up to 32 speakers\nKeyterm prompting, up to 1000 terms\n"
    findings = stt_keyterm_cap_mismatch(skill, models)
    assert len(findings) == 1
    assert findings[0].skill_evidence == "up to 100 terms"
    assert findings[0].docs_evidence == "up to 1000 terms"


def test_keyterm_missing_on_one_side_is_silent() -> None:
    assert stt_keyterm_cap_mismatch("no caps here", MODELS_1000) == []
    assert stt_keyterm_cap_mismatch("## Keyterm Prompting\nup to 100 terms", "no caps") == []


def test_fetch_text_soft_404_raises_docs_fetch_error() -> None:
    url = "https://elevenlabs.io/docs/overview/missing.md"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="# Page Not Found\n\nThis page does not exist.\n")

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(DocsFetchError, match=url),
    ):
        fetch_text(url, client=client)


def test_fetch_text_http_404_raises_status_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="missing")

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(httpx.HTTPStatusError),
    ):
        fetch_text("https://example.test/gone.md", client=client)


def test_fetch_text_ok_markdown() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="# Models\n\nFlagship.\n")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        text = fetch_text("https://example.test/models.md", client=client)
    assert text.startswith("# Models")


def test_fetch_text_accepts_yaml_front_matter() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="---\ntitle: Models\n---\n# Models\nFlagship.\n")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        text = fetch_text("https://example.test/models.md", client=client)
    assert "# Models" in text


def test_fetch_text_empty_body_is_docs_fetch_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="  \n")

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(DocsFetchError, match="empty body"),
    ):
        fetch_text("https://example.test/empty.md", client=client)


def test_fetch_text_html_body_is_docs_fetch_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text="<!DOCTYPE html><html><body>Models</body></html>",
            headers={"content-type": "text/html"},
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(DocsFetchError, match="non-markdown"),
    ):
        fetch_text("https://example.test/models.html", client=client)


def test_fetch_text_soft_404_is_case_insensitive() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="# page not found\n")

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(DocsFetchError, match="soft-404"),
    ):
        fetch_text("https://example.test/missing.md", client=client)


def test_fetch_text_missing_markdown_heading_is_docs_fetch_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="just a paragraph, no heading\n")

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(DocsFetchError, match="markdown heading"),
    ):
        fetch_text("https://example.test/prose.md", client=client)


def test_cli_exit_codes(monkeypatch: MonkeyPatch) -> None:
    def _set_fetch(models: str, tts: str, stt: str) -> None:
        def fake_fetch(url: str, **kwargs: object) -> str:
            if "models" in url:
                return models
            if "text-to-speech" in url:
                return tts
            return stt

        monkeypatch.setattr(skills_model_drift, "fetch_text", fake_fetch)

    monkeypatch.setattr("sys.argv", ["skills_model_drift.py"])
    _set_fetch(
        MODELS_WITH_DEPRECATED_TURBO + "\nKeyterm prompting, up to 1000 terms",
        TTS_SKILL_FLASH_ONLY,
        "Keyterm prompting, up to 1000 terms",
    )
    with pytest.raises(SystemExit) as silent:
        skills_model_drift.main()
    assert silent.value.code == 0

    monkeypatch.setattr("sys.argv", ["skills_model_drift.py"])
    _set_fetch(
        MODELS_WITH_DEPRECATED_TURBO + "\nKeyterm prompting, up to 1000 terms",
        TTS_SKILL_WITH_TURBO,
        "## Keyterm Prompting\nup to 100 terms",
    )
    with pytest.raises(SystemExit) as drifted:
        skills_model_drift.main()
    assert drifted.value.code == 1

    def boom(url: str, **kwargs: object) -> str:
        raise DocsFetchError(f"soft-404 from {url}: # Page Not Found")

    monkeypatch.setattr(skills_model_drift, "fetch_text", boom)
    monkeypatch.setattr("sys.argv", ["skills_model_drift.py"])
    with pytest.raises(SystemExit) as failed:
        skills_model_drift.main()
    assert failed.value.code == 2


def test_cli_invalid_url_exits_2(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["skills_model_drift.py", "--models-url", "http://\x00invalid"],
    )
    with pytest.raises(SystemExit) as failed:
        skills_model_drift.main()
    assert failed.value.code == 2
