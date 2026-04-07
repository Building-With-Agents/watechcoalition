"""Week 7 analytics aggregations (Pair B — sector / geo / salary percentiles)."""

from agents.analytics.aggregators.geo_demand import compute_geo_demand_weekly
from agents.analytics.aggregators.salary_percentiles import SALARY_VALUE_SQL, compute_salary_percentiles
from agents.analytics.aggregators.sector_weekly import compute_sector_summary_weekly

__all__ = [
    "SALARY_VALUE_SQL",
    "compute_geo_demand_weekly",
    "compute_salary_percentiles",
    "compute_sector_summary_weekly",
]
