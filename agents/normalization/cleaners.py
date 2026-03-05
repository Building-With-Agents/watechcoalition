"""Normalization utility functions — text cleaning, salary parsing, date/location normalization."""

from __future__ import annotations

import re
from datetime import UTC, datetime

# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    if not text:
        return ""
    return _HTML_TAG_RE.sub("", text)


def clean_whitespace(text: str) -> str:
    """Normalize whitespace: collapse runs, strip leading/trailing."""
    if not text:
        return ""
    return _WHITESPACE_RE.sub(" ", text).strip()


def clean_text(text: str) -> str:
    """Strip HTML then normalize whitespace."""
    return clean_whitespace(strip_html(text))


# ---------------------------------------------------------------------------
# Salary parsing
# ---------------------------------------------------------------------------

# Match patterns like "$120k", "$120,000", "$50/hr", "$120k-160k", "$120,000 - $160,000/year"
_SALARY_NUM_RE = re.compile(
    r"\$?\s*([\d,]+\.?\d*)\s*[kK]?",
)
_SALARY_RANGE_RE = re.compile(
    r"\$?\s*([\d,]+\.?\d*)\s*[kK]?\s*[-–—to]+\s*\$?\s*([\d,]+\.?\d*)\s*[kK]?",
    re.IGNORECASE,
)
_PERIOD_MAP = {
    "year": "annual", "yr": "annual", "annual": "annual", "annually": "annual",
    "per year": "annual", "/year": "annual", "/yr": "annual",
    "hour": "hourly", "hr": "hourly", "hourly": "hourly",
    "per hour": "hourly", "/hour": "hourly", "/hr": "hourly",
    "month": "monthly", "mo": "monthly", "monthly": "monthly",
    "per month": "monthly", "/month": "monthly", "/mo": "monthly",
}


def _parse_number(s: str) -> float | None:
    """Parse a salary number string, handling 'k' suffix and commas."""
    if not s:
        return None
    s = s.replace(",", "").strip()
    try:
        val = float(s)
    except ValueError:
        return None
    return val


def parse_salary(raw: str | None) -> dict:
    """Extract salary_min, salary_max, salary_currency, salary_period from a raw salary string.

    Returns a dict with keys: salary_min, salary_max, salary_currency, salary_period.
    Any field that can't be parsed is None.
    """
    result: dict = {
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "salary_period": None,
    }
    if not raw:
        return result

    raw_lower = raw.lower()

    # Detect currency
    if "$" in raw or "usd" in raw_lower:
        result["salary_currency"] = "USD"
    elif "€" in raw or "eur" in raw_lower:
        result["salary_currency"] = "EUR"
    elif "£" in raw or "gbp" in raw_lower:
        result["salary_currency"] = "GBP"

    # Detect period
    for keyword, period in _PERIOD_MAP.items():
        if keyword in raw_lower:
            result["salary_period"] = period
            break

    # Try range first: "$120k - $160k"
    range_match = _SALARY_RANGE_RE.search(raw)
    if range_match:
        min_str, max_str = range_match.group(1), range_match.group(2)
        min_val = _parse_number(min_str)
        max_val = _parse_number(max_str)

        # Handle "k" suffix
        raw_after_min = raw[range_match.start(1):range_match.end(1) + 1].lower()
        raw_after_max = raw[range_match.start(2):range_match.end(2) + 1].lower()
        if min_val and ("k" in raw_after_min or (min_val < 1000 and result.get("salary_period") == "annual")):
            min_val *= 1000
        if max_val and ("k" in raw_after_max or (max_val < 1000 and result.get("salary_period") == "annual")):
            max_val *= 1000

        result["salary_min"] = min_val
        result["salary_max"] = max_val

        # Default period for large numbers
        if result["salary_period"] is None and min_val and min_val > 500:
            result["salary_period"] = "annual"

        return result

    # Single number: "$120k" or "$50/hr"
    nums = _SALARY_NUM_RE.findall(raw)
    if nums:
        val = _parse_number(nums[0])
        if val:
            # Check for k suffix
            idx = raw.find(nums[0])
            after = raw[idx + len(nums[0]):idx + len(nums[0]) + 2].lower() if idx >= 0 else ""
            if "k" in after:
                val *= 1000
            result["salary_min"] = val
            result["salary_max"] = val

            if result["salary_period"] is None and val > 500:
                result["salary_period"] = "annual"

    return result


# ---------------------------------------------------------------------------
# Date normalization
# ---------------------------------------------------------------------------

_DATE_FORMATS = [
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%m-%d-%Y",
    "%d/%m/%Y",
    "%B %d, %Y",
    "%b %d, %Y",
]


def normalize_date(raw: str | None) -> datetime | None:
    """Parse various date formats into a timezone-aware datetime (UTC)."""
    if not raw:
        return None
    raw = raw.strip()
    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# Employment type normalization
# ---------------------------------------------------------------------------

_EMPLOYMENT_TYPE_MAP = {
    "full-time": "full_time", "full_time": "full_time", "fulltime": "full_time",
    "ft": "full_time", "permanent": "full_time",
    "part-time": "part_time", "part_time": "part_time", "parttime": "part_time",
    "pt": "part_time",
    "contract": "contract", "contractor": "contract", "freelance": "contract",
    "temporary": "temporary", "temp": "temporary",
    "internship": "internship", "intern": "internship",
}


def normalize_employment_type(raw: str | None) -> str:
    """Map raw employment type strings to standard enum values."""
    if not raw:
        return "unknown"
    key = raw.strip().lower().replace("'", "").lstrip("n")  # handle Prisma default "N'full-time'"
    return _EMPLOYMENT_TYPE_MAP.get(key, "unknown")


# ---------------------------------------------------------------------------
# Location normalization
# ---------------------------------------------------------------------------

def normalize_location(raw: str | None) -> str:
    """Clean and standardize location strings."""
    if not raw:
        return ""
    # Basic cleanup: strip, collapse whitespace, normalize common patterns
    location = clean_whitespace(raw)
    # Remove "Remote" prefix duplications like "Remote - Remote"
    if location.lower().startswith("remote - remote"):
        location = "Remote"
    return location
