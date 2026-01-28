from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

NUMBER_RE = re.compile(r"(?<!\w)[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
PERCENT_RE = re.compile(r"%|percent|percentage", re.IGNORECASE)

CURRENCY_RE = re.compile(r"\$|USD|US\$|EUR|CNY|RMB|HKD", re.IGNORECASE)
SCALE_RE = re.compile(r"\b(thousand|million|billion|trillion|k|m|b)\b", re.IGNORECASE)

METRICS = [
    "revenue",
    "sales",
    "income",
    "net income",
    "profit",
    "earnings",
    "assets",
    "liabilities",
    "margin",
]

UNIT_SCALE = {
    "thousand": 1e3,
    "k": 1e3,
    "million": 1e6,
    "m": 1e6,
    "billion": 1e9,
    "b": 1e9,
    "trillion": 1e12,
}


@dataclass
class Fact:
    qid: str
    chunk_id: str
    metric: Optional[str]
    entity: Optional[str]
    year: Optional[int]
    period: Optional[str]
    value: float
    unit: Optional[str]
    raw_span: str
    confidence: float
    inferred_year: bool = False


@dataclass
class ExtractStats:
    total_facts: int = 0
    inferred_year: int = 0
    missing_year: int = 0
    missing_unit: int = 0


def parse_number(num_str: str) -> float:
    return float(num_str.replace(",", ""))


def detect_unit(window: str, percent_window: str) -> Tuple[Optional[str], float]:
    unit = None
    scale = 1.0

    if PERCENT_RE.search(percent_window):
        return "%", 1.0

    if CURRENCY_RE.search(window):
        unit = "USD"

    scale_match = SCALE_RE.search(window)
    if scale_match:
        scale_key = scale_match.group(1).lower()
        scale = UNIT_SCALE.get(scale_key, 1.0)

    return unit, scale


def detect_metric(window: str) -> Optional[str]:
    lower = window.lower()
    for m in METRICS:
        if m in lower:
            return m
    return None


def extract_entity(query: str) -> Optional[str]:
    match = re.search(r"\b[A-Z]{2,6}\b", query)
    if match:
        return match.group(0)
    return None


def extract_facts_from_text(
    qid: str,
    chunk_id: str,
    text: str,
    query: str,
    year_candidates: Optional[List[int]] = None,
) -> List[Fact]:
    facts = []
    stats = ExtractStats()

    if year_candidates is None:
        year_candidates = [int(m.group(0)) for m in YEAR_RE.finditer(query)]
    entity = extract_entity(query)

    for match in NUMBER_RE.finditer(text):
        num_str = match.group(0)
        value = parse_number(num_str)
        start = max(match.start() - 40, 0)
        end = min(match.end() + 40, len(text))
        window = text[start:end]

        years = [int(m.group(0)) for m in YEAR_RE.finditer(window)]
        year = years[0] if years else None
        inferred = False
        if year is None and year_candidates:
            year = year_candidates[0]
            inferred = True

        unit_window = text[max(match.start() - 10, 0) : min(match.end() + 15, len(text))]
        percent_window = text[max(match.start() - 2, 0) : min(match.end() + 10, len(text))]
        unit, scale = detect_unit(unit_window, percent_window)
        metric = detect_metric(window)
        value_scaled = value * scale

        confidence = 0.6
        if unit:
            confidence += 0.15
        if year:
            confidence += 0.15
        if inferred:
            confidence -= 0.2
        confidence = max(0.0, min(1.0, confidence))

        raw_span = window.strip()[:120]

        fact = Fact(
            qid=qid,
            chunk_id=chunk_id,
            metric=metric,
            entity=entity,
            year=year,
            period=None,
            value=value_scaled,
            unit=unit,
            raw_span=raw_span,
            confidence=confidence,
            inferred_year=inferred,
        )
        facts.append(fact)

        stats.total_facts += 1
        if inferred:
            stats.inferred_year += 1
        if year is None:
            stats.missing_year += 1
        if unit is None:
            stats.missing_unit += 1

    return facts


def facts_to_dicts(facts: Iterable[Fact]) -> List[Dict[str, object]]:
    return [fact.__dict__ for fact in facts]


def merge_stats(stats_list: Iterable[ExtractStats]) -> ExtractStats:
    total = ExtractStats()
    for s in stats_list:
        total.total_facts += s.total_facts
        total.inferred_year += s.inferred_year
        total.missing_year += s.missing_year
        total.missing_unit += s.missing_unit
    return total
