from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

COMPARE_KEYWORDS = ["compare", "versus", "vs", "difference", "higher", "lower", "increase", "decrease", "growth", "change", "yoy"]

YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
PERCENT_RE = re.compile(r"%")


@dataclass
class PlanResult:
    query_type: str
    has_years: bool
    has_percent: bool
    has_compare: bool


class StepPlanner:
    def __init__(self, compare_keywords: Optional[list[str]] = None) -> None:
        self.compare_keywords = compare_keywords or COMPARE_KEYWORDS

    def plan(self, query: str) -> PlanResult:
        """Classify query intent to guide multi-step retrieval behavior."""
        q_lower = query.lower()
        has_years = bool(YEAR_RE.findall(query))
        has_percent = bool(PERCENT_RE.search(query))
        has_compare = any(k in q_lower for k in self.compare_keywords)

        if has_compare:
            query_type = "COMPARE"
        elif has_years and has_percent:
            query_type = "TREND"
        elif has_years:
            query_type = "FACT"
        else:
            query_type = "OTHER"

        return PlanResult(query_type=query_type, has_years=has_years, has_percent=has_percent, has_compare=has_compare)
