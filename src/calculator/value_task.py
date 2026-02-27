from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from calculator.combo_types import (
    REASON_EMPTY_FACTS,
    REASON_NO_CONFIDENT_FACT,
    REASON_OK,
    REASON_QUERY_NOT_NUMERIC,
    STATUS_NO_CANDIDATE,
    STATUS_NO_FACTS,
    STATUS_NO_NUMERIC_INTENT,
    STATUS_OK,
    ValuePrediction,
)
from calculator.extract import Fact

YEAR_HINT_RE = re.compile(r"\b(19|20)\d{2}\b")
PERCENT_HINT_RE = re.compile(
    r"%|\bpercent\b|\bpercentage\b|\bpct\b",
    re.IGNORECASE,
)

NUMERIC_INTENT_TERMS = [
    "yoy",
    "year over year",
    "growth",
    "increase",
    "decrease",
    "difference",
    "diff",
    "delta",
    "change",
    "share",
    "portion",
    "ratio",
    "multiple",
    "times",
    "how much",
    "how many",
    "what is",
    "value",
    "number",
]

DEFAULT_WEIGHTS = {
    "metric_present": 0.05,
    "year_match": 0.20,
    "year_mismatch": 0.10,
    "year_missing": 0.05,
    "percent_match": 0.15,
    "percent_mismatch": 0.12,
    "unit_match": 0.10,
    "unit_mismatch": 0.08,
    "inferred_year_penalty": 0.08,
}


def year_hint(query: str) -> List[int]:
    return sorted({int(match.group(0)) for match in YEAR_HINT_RE.finditer(query or "")})


def percent_hint(query: str) -> bool:
    return bool(PERCENT_HINT_RE.search(query or ""))


def unit_hint(query: str) -> Optional[str]:
    q = (query or "").lower()
    if PERCENT_HINT_RE.search(q):
        return "%"
    if any(token in q for token in ["usd", "us$", "$"]):
        return "USD"
    if any(token in q for token in ["cny", "rmb"]):
        return "CNY"
    if any(token in q for token in ["hkd"]):
        return "HKD"
    if any(token in q for token in ["eur"]):
        return "EUR"
    return None


def numeric_intent(query: str) -> bool:
    q = (query or "").lower().strip()
    if not q:
        return False
    has_digit = bool(re.search(r"\d", q))
    has_keyword = any(token in q for token in NUMERIC_INTENT_TERMS)
    return has_keyword or has_digit or percent_hint(q) or (unit_hint(q) is not None)


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_unit(unit: Optional[str]) -> Optional[str]:
    if unit is None:
        return None
    raw = str(unit).strip().lower()
    if raw in {"%", "percent", "percentage", "pct"}:
        return "%"
    if raw in {"usd", "us$", "$"}:
        return "USD"
    if raw in {"cny", "rmb"}:
        return "CNY"
    if raw in {"hkd"}:
        return "HKD"
    if raw in {"eur"}:
        return "EUR"
    return raw or None


def _resolve_weights(cfg: Dict[str, Any]) -> Dict[str, float]:
    merged = dict(DEFAULT_WEIGHTS)
    raw = cfg.get("weights", {})
    if not isinstance(raw, dict):
        return merged
    for key, default_value in DEFAULT_WEIGHTS.items():
        if key in raw:
            merged[key] = _to_float(raw.get(key), default_value)
    return merged


def _score_fact(
    fact: Fact,
    *,
    years: List[int],
    wants_percent: bool,
    wants_unit: Optional[str],
    weights: Dict[str, float],
) -> Tuple[float, bool]:
    score = float(fact.confidence)
    if fact.metric not in {None, ""}:
        score += weights["metric_present"]

    matched_year = False
    if years:
        if fact.year in years:
            score += weights["year_match"]
            matched_year = True
        elif fact.year is None:
            score -= weights["year_missing"]
        else:
            score -= weights["year_mismatch"]

    if fact.inferred_year:
        score -= weights["inferred_year_penalty"]

    fact_unit = _normalize_unit(fact.unit)
    if wants_percent:
        if fact_unit == "%":
            score += weights["percent_match"]
        elif fact_unit is not None:
            score -= weights["percent_mismatch"]

    if wants_unit is not None:
        if fact_unit == wants_unit:
            score += weights["unit_match"]
        elif fact_unit is not None:
            score -= weights["unit_mismatch"]

    return score, matched_year


def format_result_line(value: Optional[float], unit: Optional[str]) -> str:
    if value is None:
        return "Result: N/A"
    return f"Result: {value} {unit or ''}".strip()


def predict_value_for_query(
    query: str,
    facts_clean: Sequence[Fact],
    cfg: Optional[Dict[str, Any]] = None,
) -> ValuePrediction:
    config = cfg or {}
    if not numeric_intent(query):
        return STATUS_NO_NUMERIC_INTENT, None, None, 0.0, REASON_QUERY_NOT_NUMERIC
    if not facts_clean:
        return STATUS_NO_FACTS, None, None, 0.0, REASON_EMPTY_FACTS

    min_conf = max(0.0, min(1.0, _to_float(config.get("min_conf", 0.0), 0.0)))
    candidate_facts = [fact for fact in facts_clean if float(fact.confidence) >= min_conf]
    if not candidate_facts:
        return STATUS_NO_CANDIDATE, None, None, 0.0, REASON_NO_CONFIDENT_FACT

    years = year_hint(query)
    wants_percent = percent_hint(query)
    wants_unit = unit_hint(query)
    weights = _resolve_weights(config)

    scored_rows = []
    for idx, fact in enumerate(candidate_facts):
        score, matched_year = _score_fact(
            fact,
            years=years,
            wants_percent=wants_percent,
            wants_unit=wants_unit,
            weights=weights,
        )
        scored_rows.append(
            (
                score,
                float(fact.confidence),
                1 if matched_year else 0,
                1 if not fact.inferred_year else 0,
                -idx,
                fact,
            )
        )

    scored_rows.sort(reverse=True)
    best_fact = scored_rows[0][-1]
    best_unit = best_fact.unit
    if best_unit is None and wants_percent:
        best_unit = "%"
    confidence = max(0.0, min(1.0, float(best_fact.confidence)))
    return STATUS_OK, float(best_fact.value), best_unit, confidence, REASON_OK
