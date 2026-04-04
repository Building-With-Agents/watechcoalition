"""Analytics aggregators — builders for aggregate tables (ARCHITECTURE_DEEP / CLAUDE layout)."""

from agents.analytics.aggregators.demand_weekly import (
    refresh_skill_demand_weekly,
    refresh_tool_demand_weekly,
)

__all__ = [
    "refresh_skill_demand_weekly",
    "refresh_tool_demand_weekly",
]
