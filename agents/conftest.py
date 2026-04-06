"""Root conftest for the agents package.

Pytest discovers this file automatically for ALL test subdirectories
under agents/, ensuring .env is loaded before any test collection.
"""

from __future__ import annotations

from agents.common.env import load_repo_root_dotenv

# Load only the canonical repo-root .env before test collection so skip markers
# and integration fixtures all resolve against the same local configuration.
load_repo_root_dotenv()
