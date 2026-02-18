from __future__ import annotations

from scripts.build_subsets import extract_years, has_two_distinct_years


def test_extract_years_returns_full_year_strings() -> None:
    query = "compare 2019 vs 2020 revenue"
    years = extract_years(query)
    assert set(years) == {"2019", "2020"}
    assert len(set(years)) >= 2


def test_single_year_is_not_marked_as_two_years() -> None:
    query = "compare revenue in 2020"
    assert has_two_distinct_years(query) is False


def test_no_year_is_not_marked_as_two_years() -> None:
    query = "compare revenue trend"
    assert has_two_distinct_years(query) is False
