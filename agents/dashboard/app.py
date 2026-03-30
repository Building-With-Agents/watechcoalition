"""Streamlit entry point (Week 6 runbook).

Run from repo root:
    streamlit run agents/dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Streamlit puts ``agents/dashboard`` on sys.path, not the repo root, so
# ``import agents`` fails unless we add the parent of the ``agents`` package.
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from agents.dashboard.streamlit_app import main

if __name__ == "__main__":
    main()
