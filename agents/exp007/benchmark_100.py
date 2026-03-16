"""
EXP-007 Day 1c: Run 100 events through each candidate and measure latency.

Uses fixture postings (repeats to reach 100). Reports total time, p50, p95 per run.

Run from repo root: python agents/exp007/benchmark_100.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Path bootstrap
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import structlog  # noqa: E402

from agents.exp007.langgraph_runner import run_two_agent_langgraph  # noqa: E402
from agents.exp007.pure_python_runner import run_two_agent_pure_python  # noqa: E402

log = structlog.get_logger()
N = 100


def load_postings() -> list[tuple[dict, str]]:
    fixtures_dir = Path(__file__).resolve().parent.parent / "data" / "fixtures"
    fallback = fixtures_dir / "fallback_scrape_sample.json"
    if not fallback.exists():
        return []
    data = json.loads(fallback.read_text(encoding="utf-8"))
    return [(item, str(item.get("posting_id", i))) for i, item in enumerate(data)]


def p50(ms: list[float]) -> float:
    if not ms:
        return 0.0
    s = sorted(ms)
    return s[len(s) // 2]


def p95(ms: list[float]) -> float:
    if not ms:
        return 0.0
    s = sorted(ms)
    return s[int(len(s) * 0.95)] if len(s) > 1 else s[0]


def main() -> int:
    postings = load_postings()
    if not postings:
        log.error("benchmark_no_fixtures", note="No fixture postings found.")
        return 1

    # Build list of 100 (posting, correlation_id)
    runs = [postings[i % len(postings)] for i in range(N)]

    # LangGraph
    latencies_lg: list[float] = []
    t0 = time.perf_counter()
    for posting, cid in runs:
        t_start = time.perf_counter()
        run_two_agent_langgraph(posting, correlation_id=cid)
        latencies_lg.append((time.perf_counter() - t_start) * 1000)
    total_lg = (time.perf_counter() - t0) * 1000

    # Pure Python
    latencies_pp: list[float] = []
    t0 = time.perf_counter()
    for posting, cid in runs:
        t_start = time.perf_counter()
        run_two_agent_pure_python(posting, correlation_id=cid)
        latencies_pp.append((time.perf_counter() - t_start) * 1000)
    total_pp = (time.perf_counter() - t0) * 1000

    log.info(
        "benchmark_complete",
        n_events=N,
        langgraph_total_ms=round(total_lg, 0),
        langgraph_p50_ms=round(p50(latencies_lg), 2),
        langgraph_p95_ms=round(p95(latencies_lg), 2),
        pure_python_total_ms=round(total_pp, 0),
        pure_python_p50_ms=round(p50(latencies_pp), 2),
        pure_python_p95_ms=round(p95(latencies_pp), 2),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
