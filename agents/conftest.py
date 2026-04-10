"""Root conftest for the agents package.

Pytest discovers this file automatically for ALL test subdirectories
under agents/, ensuring .env is loaded before any test collection.
"""

from __future__ import annotations

import pytest

from agents.common.env import load_repo_root_dotenv

# Canonical repo-root .env before collection so skip markers and integration
# fixtures resolve against the same local configuration.
load_repo_root_dotenv()


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="Run enrichment promotion tests that call real Azure/OpenAI (slow; requires keys).",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "live_llm: integration test using real LLM; run with pytest --live",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--live", default=False):
        return
    skip_live = pytest.mark.skip(reason="pass --live to run live_llm promotion tests")
    for item in items:
        if "live_llm" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture(autouse=True)
def _analytics_minimum_data_guard_off_for_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Analytics agent tests do not require 50+ enriched rows on the dev database."""
    monkeypatch.setenv("ANALYTICS_DISABLE_MINIMUM_DATA_GUARD", "1")
