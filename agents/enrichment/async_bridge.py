"""Run async adapter coroutines from synchronous EnrichmentAgent code.

``asyncio.run`` must not be used when an event loop is already running; Phase 1 pipeline
invokes ``process`` from sync contexts only. Phase 2 may move the agent to async execution.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


def run_coroutine(coro: Coroutine[Any, Any, T]) -> T:
    """Execute one coroutine to completion (new event loop per call when none is running)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    msg = (
        "Cannot run enrichment external adapters: an event loop is already running. "
        "Call EnrichmentAgent.process from a synchronous context, or refactor to async."
    )
    raise RuntimeError(msg)
