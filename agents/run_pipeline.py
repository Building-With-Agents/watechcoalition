"""
Entrypoint for the Week 2 walking-skeleton pipeline.

Run from repository root.

Examples:
  python -m agents.run_pipeline
  python -m agents.run_pipeline --health
  python -m agents.run_pipeline --save-events agents/data/rendered/last_pipeline_events.json

Note:
  `--save-events` resolves relative to the current working directory.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import structlog

from agents.common.pipeline.runner import health_check_all, run_pipeline


def _configure_logging() -> None:
    # Default to INFO so regular runs show stage timeline while DEBUG includes per-agent emission details.
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(level))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Job Intelligence Engine walking skeleton")
    parser.add_argument(
        "--health",
        "-H",
        action="store_true",
        help="Run health checks only (does not execute pipeline stages).",
    )
    parser.add_argument(
        "--save-events",
        type=str,
        default="",
        help="Optional path to persist emitted journey events as JSON.",
    )
    return parser


def _write_events(path: str, events: list[dict[str, Any]]) -> Path:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=True, indent=2)
    return out_path


def _run_health_check() -> int:
    result = health_check_all()
    for agent_id, health in result.items():
        sys.stdout.write(
            f"  {agent_id}: {health.get('status', '?')}  last_run={health.get('last_run', '—')}\n"
        )
    return 0


def _run_pipeline_once(save_events_path: str) -> int:
    events = run_pipeline()
    if save_events_path:
        saved_path = _write_events(save_events_path, events)
        sys.stdout.write(f"Saved events: {saved_path}\n")
    sys.stdout.write(f"Run complete: {len(events)} events\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    _configure_logging()
    args = _build_parser().parse_args(argv)
    if args.health:
        return _run_health_check()
    return _run_pipeline_once(args.save_events)


if __name__ == "__main__":
    sys.exit(main())
