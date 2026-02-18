from __future__ import annotations

from retrieval.query_expansion import QueryExpander


def test_expand_disabled_returns_original_only() -> None:
    expander = QueryExpander(enabled=False)
    query = "Compare MS revenue in 2020"
    expanded = expander.expand(query, seed_chunks=[{"text": "Morgan Stanley (MS) in 2020."}])
    assert expanded == [query]


def test_abbrev_expansion_adds_long_form() -> None:
    expander = QueryExpander(
        enabled=True,
        max_queries=3,
        abbrev_enabled=True,
        prf_year_enabled=False,
        abbrev_map={"MS": "Morgan Stanley"},
    )
    expanded = expander.expand("MS revenue growth", seed_chunks=[])
    assert len(expanded) >= 2
    assert any("Morgan Stanley" in q for q in expanded[1:])


def test_prf_year_expansion_uses_seed_years() -> None:
    expander = QueryExpander(
        enabled=True,
        max_queries=3,
        abbrev_enabled=False,
        prf_year_enabled=True,
    )
    expanded = expander.expand(
        "MS revenue growth",
        seed_chunks=[{"text": "Revenue rose in 2021 and stayed strong in 2020."}],
    )
    assert len(expanded) >= 2
    assert any(("2021" in q) or ("2020" in q) for q in expanded[1:])
