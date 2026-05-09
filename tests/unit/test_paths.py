"""Tests for repository path helpers."""

from __future__ import annotations

from pathlib import Path

import eleven_demo.paths as paths_mod
from eleven_demo.paths import load_repo_dotenv, repo_root


def test_repo_root_contains_pyproject() -> None:
    root = repo_root()
    assert (root / "pyproject.toml").is_file()
    assert (root / "src" / "eleven_demo").is_dir()


def test_load_repo_dotenv_returns_root(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setattr(paths_mod, "repo_root", lambda: tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text("ELEVENLABS_API_KEY=\n", encoding="utf-8")
    result = load_repo_dotenv()
    assert result == tmp_path
