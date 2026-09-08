"""Shared pytest fixtures for unit and integration tests."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from dotenv import load_dotenv
from elevenlabs import ElevenLabs

from eleven_demo.client import get_client
from eleven_demo.config import get_settings

if TYPE_CHECKING:
    from pytest import FixtureRequest

load_dotenv()

# Unit tests must collect without a real key (CI has no .env). Integration tests
# treat this placeholder as "no live credentials".
_CI_PLACEHOLDER_API_KEY = "xi-ci-placeholder"
if not os.environ.get("ELEVENLABS_API_KEY", "").strip():
    os.environ["ELEVENLABS_API_KEY"] = _CI_PLACEHOLDER_API_KEY


def _vcr_cassette_yaml_path(request: FixtureRequest) -> Path:
    """Resolve cassette path matching pytest-vcr defaults.

    Mirrors ``pytest_vcr``: ``vcr_cassette_dir`` = ``<test_file_dir>/cassettes``,
    ``vcr_cassette_name`` = ``ClassName.function_name`` or ``function_name``, suffix ``.yaml``.
    """

    test_dir = Path(request.node.path).parent
    cassette_dir = test_dir / "cassettes"
    cls = request.cls
    stem = f"{cls.__name__}.{request.node.name}" if cls is not None else request.node.name
    return cassette_dir / f"{stem}.yaml"


@pytest.fixture(autouse=True)
def _skip_integration_without_key(request: FixtureRequest) -> None:
    """Skip integration tests without API key when no recorded cassette exists."""

    if request.node.get_closest_marker("integration") is None:
        return

    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if api_key and api_key != _CI_PLACEHOLDER_API_KEY:
        return

    cassette = _vcr_cassette_yaml_path(request)
    if cassette.is_file():
        return

    pytest.skip(
        "ELEVENLABS_API_KEY unset and no VCR cassette found "
        f"(expected {cassette.as_posix()} once recorded)",
    )


@pytest.fixture
def mock_eleven_client() -> MagicMock:
    """MagicMock constrained to :class:`~elevenlabs.client.ElevenLabs`."""

    return MagicMock(spec=ElevenLabs)


@pytest.fixture(autouse=True)
def clear_settings_cache() -> Iterator[None]:
    """Clear cached settings and HTTP client between tests."""

    get_settings.cache_clear()
    get_client.cache_clear()
    yield
    get_settings.cache_clear()
    get_client.cache_clear()
