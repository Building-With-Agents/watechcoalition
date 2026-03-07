"""EXP-007: Multi-agent framework experiment.

Two- and three-agent pipelines in LangGraph; pure Python runner for comparison.
See docs/planning/EXP-007-plan-and-findings-template.md.
"""

from agents.exp007.langgraph_runner import (
    build_three_agent_graph,
    build_two_agent_graph,
    run_from_after_ingestion_langgraph,
    run_three_agent_langgraph,
    run_two_agent_langgraph,
)
from agents.exp007.pure_python_runner import (
    run_from_after_ingestion_pure_python,
    run_two_agent_pure_python,
)

__all__ = [
    "build_three_agent_graph",
    "build_two_agent_graph",
    "run_from_after_ingestion_langgraph",
    "run_from_after_ingestion_pure_python",
    "run_three_agent_langgraph",
    "run_two_agent_langgraph",
    "run_two_agent_pure_python",
]
