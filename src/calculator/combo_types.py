from __future__ import annotations

from typing import Dict, Literal, Optional, Tuple, TypedDict

ComboStatus = Literal["ok", "no_numeric_intent", "no_facts", "no_candidate"]
ValuePrediction = Tuple[ComboStatus, Optional[float], Optional[str], float, str]

STATUS_OK: ComboStatus = "ok"
STATUS_NO_NUMERIC_INTENT: ComboStatus = "no_numeric_intent"
STATUS_NO_FACTS: ComboStatus = "no_facts"
STATUS_NO_CANDIDATE: ComboStatus = "no_candidate"

REASON_OK = "ok_top1"
REASON_QUERY_NOT_NUMERIC = "query_not_numeric"
REASON_EMPTY_FACTS = "empty_facts"
REASON_NO_CONFIDENT_FACT = "no_fact_above_min_conf"


class FactFilterConfig(TypedDict, total=False):
    min_conf: float
    max_facts_per_group: int
    drop_year_like_values: bool | Dict[str, object]


class ValueTaskConfig(TypedDict, total=False):
    min_conf: float
    weights: Dict[str, float]
