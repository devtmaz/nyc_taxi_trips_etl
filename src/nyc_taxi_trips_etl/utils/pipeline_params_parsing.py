import re
from datetime import datetime

_YEAR_ONLY_RE = re.compile(r"^\d{4}$")
_YEAR_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_SAFETY_LOOKBACK = (
    2  # months to subtract from current month for the current year
)


def get_current_day() -> datetime:
    """Returns the current day as a datetime object."""
    return datetime.today()


def _expand_year(year: int) -> list[str]:
    """Returns all YYYY-MM strings for the given year.

    For the current year, only months up to (current_month - SAFETY_LOOKBACK)
    are included.

    Args:
        year: The year to expand as integer.
    Returns:
        A list of strings in the format YYYY-MM for each month of the year.
    Raises:
        ValueError: If the year is the current year and the safety lookback
        leaves no valid months.

    """
    today = get_current_day()
    if year == today.year:
        max_month = today.month - _SAFETY_LOOKBACK
        if max_month < 1:
            raise ValueError(
                f"Year {year} is the current year but the safety lookback of "
                f"{_SAFETY_LOOKBACK} months leaves no valid months to extract."
            )
    else:
        max_month = 12

    return [f"{year}-{m:02d}" for m in range(1, max_month + 1)]


def parse_and_expand_year_months(year_months_str: str) -> set[str]:
    """Validates, expands, and deduplicates a year-months input string.

    Each comma-separated token must be either:
    - ``YYYY``    — expanded to every month of that year (current year: up to
                    current_month - SAFETY_LOOKBACK).
    - ``YYYY-MM`` — kept as-is; month must be 01-12.

    Args:
        year_months_str: Comma-separated year or year-month values.

    Returns:
        A set of ``YYYY-MM`` strings with no duplicates.

    Raises:
        ValueError: If any token does not match a recognised format, or if the
                    current-year safety lookback leaves no valid months.
    """
    result: set[str] = set()

    tokens = [t.strip() for t in year_months_str.split(",")]

    for token in tokens:
        if _YEAR_MONTH_RE.match(token):
            result.add(token)
        elif _YEAR_ONLY_RE.match(token):
            result.update(_expand_year(int(token)))
        else:
            raise ValueError(
                f"Invalid token '{token}'. "
                "Expected 'YYYY' or 'YYYY-MM' (comma-separated). "
                "Space-separated values without commas are not supported."
            )

    return result
