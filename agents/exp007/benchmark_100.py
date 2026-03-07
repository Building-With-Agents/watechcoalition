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

from agents.exp007.langgraph_runner import run_two_agent_langgraph
from agents.exp007.pure_python_runner import run_two_agent_pure_python

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
        print("No fixture postings found.", file=sys.stderr)
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

    print(f"Benchmark: {N} events per candidate")
    print("  LangGraph:   total={:.0f} ms  p50={:.2f} ms  p95={:.2f} ms".format(
        total_lg, p50(latencies_lg), p95(latencies_lg)))
    print("  Pure Python: total={:.0f} ms  p50={:.2f} ms  p95={:.2f} ms".format(
        total_pp, p50(latencies_pp), p95(latencies_pp)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
