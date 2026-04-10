"""Analytics aggregators — builders for aggregate tables (ARCHITECTURE_DEEP / CLAUDE layout).

Week 7 Pair A: skill/tool demand, velocity, co-occurrence.
Week 7 Pair B: sector summary, geo demand, salary percentiles.
"""

from agents.analytics.aggregators.co_occurrence import refresh_skill_co_occurrence
from agents.analytics.aggregators.demand_weekly import (
    refresh_skill_demand_weekly,
    refresh_tool_demand_weekly,
)
from agents.analytics.aggregators.geo_demand import compute_geo_demand_weekly
from agents.analytics.aggregators.salary_percentiles import SALARY_VALUE_SQL, compute_salary_percentiles
from agents.analytics.aggregators.sector_weekly import compute_sector_summary_weekly
from agents.analytics.aggregators.velocity import refresh_skill_velocity

__all__ = [
    "SALARY_VALUE_SQL",
    "compute_geo_demand_weekly",
    "compute_salary_percentiles",
    "compute_sector_summary_weekly",
    "refresh_skill_co_occurrence",
    "refresh_skill_demand_weekly",
    "refresh_tool_demand_weekly",
    "refresh_skill_velocity",
]
