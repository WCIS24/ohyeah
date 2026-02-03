from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

METRIC_SYNONYMS = {
    "revenue": ["revenue", "sales"],
    "profit": ["profit", "net income", "earnings"],
    "growth": ["growth", "increase", "decrease", "change"],
}


@dataclass
class Refinement:
    refined_query: str
    reason: str


def refine_query(
    query: str,
    gap_type: str,
    missing_years: List[str],
    missing_entity: Optional[str],
) -> Refinement:
    """Refine query by appending missing years/entities or metric synonyms."""
    if gap_type == "MISSING_YEAR" and missing_years:
        return Refinement(refined_query=f"{query} {missing_years[0]}", reason="append_missing_year")
    if gap_type == "MISSING_ENTITY" and missing_entity:
        return Refinement(refined_query=f"{query} {missing_entity}", reason="append_missing_entity")
    if gap_type == "MISSING_METRIC":
        # Append a small metric synonym list
        extra = " ".join(sorted({w for vals in METRIC_SYNONYMS.values() for w in vals}))
        return Refinement(refined_query=f"{query} {extra}", reason="append_metric_synonyms")
    return Refinement(refined_query=query, reason="no_change")
