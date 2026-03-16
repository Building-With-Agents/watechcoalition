"""Root conftest for the agents package.

Pytest discovers this file automatically for ALL test subdirectories
under agents/, ensuring .env is loaded before any test collection.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# Load .env before test modules are collected so that @pytest.mark.skipif
# decorators that check os.getenv("PYTHON_DATABASE_URL") see the real value.
# Try repo root first, then walk upward from CWD (handles worktrees).
_REPO_ROOT = Path(__file__).resolve().parents[1]
_dotenv_path = _REPO_ROOT / ".env"
if not _dotenv_path.exists():
    _dotenv_path = find_dotenv(usecwd=True) or ""
load_dotenv(_dotenv_path)
