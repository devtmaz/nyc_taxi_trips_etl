"""Unit tests for src/utils/pipeline_params_parsing.py."""

import pytest
from datetime import datetime
from unittest.mock import patch

from nyc_taxi_trips_etl.utils.pipeline_params_parsing import (
    _expand_year,
    parse_and_expand_year_months,
)

# Fixed "today" used as the default frozen date: 2026-06-29
_MOCK_TODAY = datetime(2026, 6, 29)


@pytest.fixture(autouse=True)
def _freeze_today():
    """Freeze datetime.today() to _MOCK_TODAY (2026-06-29) for every test.
    Tests that need a different date accept this fixture as a parameter
    and update today.return_value before calling the function.
    """
    with patch(
        "nyc_taxi_trips_etl.utils.pipeline_params_parsing.get_current_day"
    ) as mock_get_current_day:
        mock_get_current_day.return_value = _MOCK_TODAY
        yield mock_get_current_day


# ---------------------------------------------------------------------------
# _expand_year
# ---------------------------------------------------------------------------


class TestExpandYear:
    """Tests for the _expand_year helper."""

    def test_past_year_returns_all_12_months(self):
        result = _expand_year(2023)
        assert result == [f"2023-{m:02d}" for m in range(1, 13)]

    def test_future_year_returns_all_12_months(self):
        result = _expand_year(2027)
        assert result == [f"2027-{m:02d}" for m in range(1, 13)]

    def test_current_year_applies_safety_lookback(self):
        # mock today = 2026-06-29, lookback=2 → max_month=4
        result = _expand_year(2026)
        assert result == ["2026-01", "2026-02", "2026-03", "2026-04"]

    def test_current_year_minimum_valid_lookback(self, _freeze_today):
        # current_month=3, lookback=2 → max_month=1
        _freeze_today.return_value = datetime(2026, 3, 1)
        result = _expand_year(2026)
        assert result == ["2026-01"]

    def test_current_year_december_applies_lookback(self, _freeze_today):
        # current_month=12, lookback=2 → max_month=10
        _freeze_today.return_value = datetime(2026, 12, 1)
        result = _expand_year(2026)
        assert result == [f"2026-{m:02d}" for m in range(1, 11)]

    def test_current_year_month_2_raises_value_error(self, _freeze_today):
        _freeze_today.return_value = datetime(2026, 2, 1)
        with pytest.raises(ValueError, match="safety lookback"):
            _expand_year(2026)

    def test_current_year_month_1_raises_value_error(self, _freeze_today):
        _freeze_today.return_value = datetime(2026, 1, 1)
        with pytest.raises(ValueError, match="safety lookback"):
            _expand_year(2026)


# ---------------------------------------------------------------------------
# parse_and_expand_year_months
# ---------------------------------------------------------------------------


class TestParseAndExpandYearMonths:
    """Tests for the parse_and_expand_year_months function."""

    @pytest.mark.parametrize(
        "year_month",
        [
            pytest.param("2025-01", id="january"),
            pytest.param("2025-12", id="december"),
            pytest.param("2025-09", id="leading_zero_month"),
        ],
    )
    def test_single_year_month(self, year_month):
        assert parse_and_expand_year_months(year_month) == {year_month}

    @pytest.mark.parametrize(
        "input_str, expected",
        [
            pytest.param(
                "2025-01, 2025-02", {"2025-01", "2025-02"}, id="with_spaces"
            ),
            pytest.param(
                "2025-01,2025-02", {"2025-01", "2025-02"}, id="no_spaces"
            ),
            pytest.param(
                "2025-01 ,2025-02", {"2025-01", "2025-02"}, id="mixed_spacing"
            ),
        ],
    )
    def test_multiple_year_months(self, input_str, expected):
        assert parse_and_expand_year_months(input_str) == expected

    @pytest.mark.parametrize(
        "year_str, expected",
        [
            pytest.param(
                "2025", {f"2025-{m:02d}" for m in range(1, 13)}, id="past_year"
            ),
            pytest.param(
                "2026",
                {"2026-01", "2026-02", "2026-03", "2026-04"},
                id="current_year_with_lookback",
            ),
        ],
    )
    def test_year_expands_to_months(self, year_str, expected):
        assert parse_and_expand_year_months(year_str) == expected

    @pytest.mark.parametrize(
        "input_str, expected",
        [
            pytest.param(
                "2025, 2026-03",
                {f"2025-{m:02d}" for m in range(1, 13)} | {"2026-03"},
                id="past_year_and_explicit_month",
            ),
            pytest.param(
                "2024, 2025",
                {f"2024-{m:02d}" for m in range(1, 13)}
                | {f"2025-{m:02d}" for m in range(1, 13)},
                id="two_years",
            ),
        ],
    )
    def test_mixed_tokens(self, input_str, expected):
        assert parse_and_expand_year_months(input_str) == expected

    @pytest.mark.parametrize(
        "input_str, expected",
        [
            pytest.param(
                "2025, 2025-06",
                {f"2025-{m:02d}" for m in range(1, 13)},
                id="year_expansion_covers_explicit_month",
            ),
            pytest.param(
                "2025-03, 2025-03", {"2025-03"}, id="same_year_month_repeated"
            ),
            pytest.param(
                "2025, 2025",
                {f"2025-{m:02d}" for m in range(1, 13)},
                id="same_year_repeated",
            ),
        ],
    )
    def test_deduplication(self, input_str, expected):
        assert parse_and_expand_year_months(input_str) == expected

    # --- invalid inputs ---

    @pytest.mark.parametrize(
        "invalid_input",
        [
            pytest.param("2025-01 2025-02", id="space_separated_no_comma"),
            pytest.param("2025-13", id="month_13"),
            pytest.param("2025-00", id="month_00"),
            pytest.param("2025-01-15", id="full_date_yyyy_mm_dd"),
            pytest.param("abcd-ef", id="non_numeric"),
            pytest.param("", id="empty_string"),
            pytest.param("20251", id="year_with_extra_digit"),
            pytest.param("202", id="year_with_only_3_digits"),
        ],
    )
    def test_invalid_input_raises(self, invalid_input):
        with pytest.raises(ValueError, match="Invalid token"):
            parse_and_expand_year_months(invalid_input)
