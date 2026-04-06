"""Week 7 analytics aggregations (Pair B — sector / geo / salary percentiles)."""

from agents.analytics.aggregators.geo_demand import compute_geo_demand_weekly
from agents.analytics.aggregators.salary_percentiles import compute_salary_percentiles

__all__ = [
    "compute_geo_demand_weekly",
    "compute_salary_percentiles",
]
