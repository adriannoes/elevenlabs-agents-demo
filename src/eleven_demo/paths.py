"""Filesystem paths for repository-level tooling."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def repo_root() -> Path:
    """Return the repository root (the directory that contains ``pyproject.toml``)."""
    return Path(__file__).resolve().parent.parent.parent


def load_repo_dotenv(*, override: bool = False) -> Path:
    """Load ``.env`` from the repository root and return that root path."""
    root = repo_root()
    load_dotenv(root / ".env", override=override)
    return root
