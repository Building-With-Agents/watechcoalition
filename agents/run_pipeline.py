"""
Entrypoint for the single pipeline script. Run from repo root:

  python -m agents.run_pipeline           # Run full pipeline (calls health_check on each agent first)
  python -m agents.run_pipeline --health  # Run only health_check on all agents

Returns event list for Journey dashboard; logs to structlog. No secrets in code; config from env.
Default log level is INFO so the run shows a clean timeline; set LOG_LEVEL=DEBUG for agent *_emitted lines.
"""

import logging
import os
import sys

import structlog

# Default to INFO so default run shows timeline only (pipeline_stage_done); DEBUG shows *_emitted.
_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
_level = getattr(logging, _level_name, logging.INFO)
structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(_level))

from agents.common.pipeline.runner import health_check_all, run_pipeline

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--health", "-H"):
        result = health_check_all()
        for agent_id, h in result.items():
            print(f"  {agent_id}: {h.get('status', '?')}  last_run={h.get('last_run', '—')}")
        sys.exit(0)
    events = run_pipeline()
    print(f"Run complete: {len(events)} events")  # Optional; dashboard can consume events another way
