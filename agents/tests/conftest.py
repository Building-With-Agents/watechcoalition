# agents/tests/conftest.py
"""Ensure repo root is on path so 'from agents.*' works when running pytest from agents/."""

import sys
from pathlib import Path

# Repo root = parent of agents/
_agents_dir = Path(__file__).resolve().parent.parent
_repo_root = _agents_dir.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
