"""Shared repo-root environment helpers for agent tooling."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REPO_DOTENV_PATH = _REPO_ROOT / ".env"


def repo_root() -> Path:
    """Return the repository root directory."""
    return _REPO_ROOT


def repo_dotenv_path() -> Path:
    """Return the canonical repo-root ``.env`` path."""
    return _REPO_DOTENV_PATH


def load_repo_root_dotenv(*, override: bool = False) -> Path | None:
    """Load only the repo-root ``.env`` when present.

    This intentionally does not walk parent directories or fall back to the
    current working directory. Agent scripts and tests should treat the repo
    root ``.env`` as the single local source of truth.
    """
    if not _REPO_DOTENV_PATH.exists():
        return None
    load_dotenv(_REPO_DOTENV_PATH, override=override)
    return _REPO_DOTENV_PATH
