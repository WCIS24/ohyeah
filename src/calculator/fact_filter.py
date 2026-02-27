from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

from calculator.extract import Fact

DEFAULT_YEAR_MIN = 1900
DEFAULT_YEAR_MAX = 2099


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_unit(unit: Optional[str]) -> Optional[str]:
    if unit is None:
        return None
    normalized = str(unit).strip().lower()
    return normalized or None


def _group_key(fact: Fact) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    metric = fact.metric.strip().lower() if isinstance(fact.metric, str) else fact.metric
    entity = fact.entity.strip().lower() if isinstance(fact.entity, str) else fact.entity
    unit = _normalize_unit(fact.unit)
    return metric, entity, unit


def _is_year_like_value(value: float, min_year: int, max_year: int) -> bool:
    nearest_int = int(round(value))
    if abs(value - nearest_int) > 1e-9:
        return False
    return min_year <= nearest_int <= max_year


def drop_year_like_values(
    facts: Sequence[Fact],
    *,
    min_year: int = DEFAULT_YEAR_MIN,
    max_year: int = DEFAULT_YEAR_MAX,
) -> List[Fact]:
    kept: List[Fact] = []
    for fact in facts:
        metric_missing = fact.metric in {None, ""}
        unit_missing = fact.unit in {None, ""}
        if (
            metric_missing
            and unit_missing
            and _is_year_like_value(float(fact.value), min_year=min_year, max_year=max_year)
        ):
            continue
        kept.append(fact)
    return kept


def _drop_year_config(cfg: Dict[str, Any]) -> Tuple[bool, int, int]:
    drop_cfg = cfg.get("drop_year_like_values", True)
    if isinstance(drop_cfg, dict):
        enabled = bool(drop_cfg.get("enabled", True))
        year_min = _to_int(drop_cfg.get("min_year", DEFAULT_YEAR_MIN), DEFAULT_YEAR_MIN)
        year_max = _to_int(drop_cfg.get("max_year", DEFAULT_YEAR_MAX), DEFAULT_YEAR_MAX)
        return enabled, year_min, year_max
    return bool(drop_cfg), DEFAULT_YEAR_MIN, DEFAULT_YEAR_MAX


def filter_facts(
    query: str,
    facts: Sequence[Fact],
    cfg: Optional[Dict[str, Any]] = None,
) -> List[Fact]:
    _ = query
    config = cfg or {}
    min_conf = max(0.0, min(1.0, _to_float(config.get("min_conf", 0.0), 0.0)))
    max_per_group = _to_int(config.get("max_facts_per_group", 0), 0)
    drop_enabled, year_min, year_max = _drop_year_config(config)

    filtered = [fact for fact in facts if float(fact.confidence) >= min_conf]
    if drop_enabled:
        filtered = drop_year_like_values(filtered, min_year=year_min, max_year=year_max)

    if max_per_group <= 0:
        return list(filtered)

    grouped: Dict[Tuple[Optional[str], Optional[str], Optional[str]], List[Tuple[int, Fact]]] = (
        defaultdict(list)
    )
    for idx, fact in enumerate(filtered):
        grouped[_group_key(fact)].append((idx, fact))

    selected_rows: List[Tuple[int, Fact]] = []
    ordered_keys = sorted(grouped.keys(), key=lambda x: (x[0] or "", x[1] or "", x[2] or ""))
    for key in ordered_keys:
        ranked = sorted(
            grouped[key],
            key=lambda row: (-float(row[1].confidence), 1 if row[1].inferred_year else 0, row[0]),
        )
        selected_rows.extend(ranked[:max_per_group])

    selected_rows.sort(key=lambda row: row[0])
    return [fact for _, fact in selected_rows]
