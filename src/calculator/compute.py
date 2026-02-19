from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from calculator.extract import Fact

YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")

V1_KEYWORDS: Dict[str, List[str]] = {
    "yoy": [
        "yoy",
        "year over year",
        "growth",
        "increase",
        "decrease",
        "\u540c\u6bd4",
        "\u73af\u6bd4",
        "\u589e\u957f",
        "\u589e\u901f",
        "\u6da8\u8dcc\u5e45",
        "\u53d8\u5316\u7387",
    ],
    "diff": [
        "difference",
        "change",
        "delta",
        "diff",
        "\u5dee\u503c",
        "\u5dee\u989d",
        "\u53d8\u5316",
        "\u589e\u52a0",
        "\u51cf\u5c11",
    ],
    "share": [
        "share",
        "percentage",
        "portion",
        "\u5360\u6bd4",
        "\u6bd4\u4f8b",
        "\u4efd\u989d",
        "\u767e\u5206\u6bd4",
    ],
    "multiple": [
        "times",
        "multiple",
        "\u500d",
        "\u500d\u6570",
    ],
}

V2_PATTERNS: List[Tuple[str, str, str, float]] = [
    ("yoy_explicit", r"\byoy\b|year\s*over\s*year|\u540c\u6bd4|\u73af\u6bd4", "yoy", 0.90),
    (
        "yoy_rate",
        r"growth\s*rate|rate\s*of\s*change|increase\s*rate|decrease\s*rate|\u589e\u957f\u7387|\u589e\u901f|\u53d8\u5316\u7387",
        "yoy",
        0.70,
    ),
    (
        "diff_explicit",
        r"\bdifference\b|\bdelta\b|\bdiff\b|how\s*much\s*(?:increase|decrease|change)|\u5dee\u503c|\u5dee\u989d|\u589e\u52a0|\u51cf\u5c11",
        "diff",
        0.80,
    ),
    (
        "diff_from_to",
        r"from\s+.+\s+to\s+.+|\u4ece.+\u5230.+",
        "diff",
        0.60,
    ),
    (
        "share_explicit",
        r"\bshare\b|portion|percentage\s+of|\u5360\u6bd4|\u6bd4\u4f8b|\u4efd\u989d",
        "share",
        0.85,
    ),
    (
        "multiple_explicit",
        r"\btimes\b|\bmultiple\b|\u500d\u6570|\u591a\u5c11\u500d",
        "multiple",
        0.85,
    ),
    (
        "percent_point",
        r"percentage\s*point|\u767e\u5206\u70b9",
        "diff",
        0.70,
    ),
]


@dataclass
class TaskParseResult:
    task_type: Optional[str]
    confidence: float
    rule: Optional[str]
    mode: str
    rejected: bool = False
    scores: Dict[str, float] = field(default_factory=dict)
    rules: List[str] = field(default_factory=list)


@dataclass
class CalcResult:
    qid: str
    task_type: str
    inputs: List[Dict[str, object]]
    result_value: Optional[float]
    result_unit: Optional[str]
    explanation: str
    confidence: float
    status: str


@dataclass
class CalcTrace:
    qid: str
    task_type: str
    selected_key: Optional[Tuple]
    candidates: int
    reason: str
    parser_mode: str = "v1"
    parser_confidence: float = 0.0
    parser_rule: Optional[str] = None
    parser_rejected: bool = False
    parser_scores: Dict[str, float] = field(default_factory=dict)
    parser_rules: List[str] = field(default_factory=list)


def _contains_any(text: str, keywords: List[str]) -> Optional[str]:
    for kw in keywords:
        if kw and kw in text:
            return kw
    return None


def parse_task_v1(query: str) -> TaskParseResult:
    q = (query or "").lower()
    for task in ["yoy", "diff", "share", "multiple"]:
        hit = _contains_any(q, [k.lower() for k in V1_KEYWORDS[task]])
        if hit:
            return TaskParseResult(
                task_type=task,
                confidence=1.0,
                rule=f"v1:{task}:{hit}",
                mode="v1",
                rejected=False,
                scores={task: 1.0},
                rules=[f"v1:{task}:{hit}"],
            )
    return TaskParseResult(
        task_type=None,
        confidence=0.0,
        rule=None,
        mode="v1",
        rejected=False,
        scores={},
        rules=[],
    )


def parse_task_v2(query: str, min_conf: float) -> TaskParseResult:
    q = query or ""
    q_lower = q.lower()
    scores: Dict[str, float] = {"yoy": 0.0, "diff": 0.0, "share": 0.0, "multiple": 0.0}
    rule_hits: List[str] = []

    def hit(task: str, rule_id: str, score: float) -> None:
        scores[task] = scores.get(task, 0.0) + float(score)
        rule_hits.append(rule_id)

    for rule_id, pat, task, score in V2_PATTERNS:
        if re.search(pat, q, flags=re.IGNORECASE):
            hit(task, f"v2:{rule_id}", score)

    years = [int(m.group(0)) for m in YEAR_RE.finditer(q)]
    years = sorted(set(years))
    if len(years) >= 2:
        if any(x in q_lower for x in ["growth", "change", "increase", "decrease", "yoy"]):
            hit("yoy", "v2:two_years_plus_growth", 0.40)
        if "from" in q_lower and "to" in q_lower:
            hit("diff", "v2:two_years_from_to", 0.25)

    if any(x in q_lower for x in ["how much", "how many", "what is the"]):
        if "%" in q or "percent" in q_lower:
            hit("yoy", "v2:how_much_percent", 0.25)
            hit("share", "v2:how_much_percent", 0.15)
        else:
            hit("diff", "v2:how_much_numeric", 0.20)

    if any(x in q_lower for x in ["up", "down", "fell", "rose", "drop", "gain"]):
        hit("diff", "v2:directional_terms", 0.20)

    positive_scores = [s for s in scores.values() if s > 0]
    if not positive_scores:
        return TaskParseResult(
            task_type=None,
            confidence=0.0,
            rule=None,
            mode="v2",
            rejected=False,
            scores=scores,
            rules=rule_hits,
        )

    task_type = max(scores.items(), key=lambda kv: kv[1])[0]
    best_score = scores[task_type]
    total_score = sum(positive_scores)
    confidence = best_score / total_score if total_score > 0 else 0.0
    confidence = max(confidence, min(1.0, best_score))

    rejected = confidence < float(min_conf)
    if rejected:
        return TaskParseResult(
            task_type=None,
            confidence=confidence,
            rule=rule_hits[0] if rule_hits else None,
            mode="v2",
            rejected=True,
            scores=scores,
            rules=rule_hits,
        )
    return TaskParseResult(
        task_type=task_type,
        confidence=confidence,
        rule=rule_hits[0] if rule_hits else None,
        mode="v2",
        rejected=False,
        scores=scores,
        rules=rule_hits,
    )


def parse_task(query: str, mode: str = "v1", min_conf: float = 0.0) -> TaskParseResult:
    parser_mode = (mode or "v1").strip().lower()
    if parser_mode == "v2":
        return parse_task_v2(query, min_conf=min_conf)
    return parse_task_v1(query)


def detect_task(query: str) -> Optional[str]:
    return parse_task(query, mode="v1", min_conf=0.0).task_type


def group_facts(facts: List[Fact]) -> Dict[Tuple, List[Fact]]:
    groups: Dict[Tuple, List[Fact]] = {}
    for f in facts:
        key = (f.metric, f.entity, f.unit)
        groups.setdefault(key, []).append(f)
    return groups


def select_group(groups: Dict[Tuple, List[Fact]]) -> Tuple[Optional[Tuple], List[Fact]]:
    best_key = None
    best_group: List[Fact] = []
    for key, group in groups.items():
        if len(group) > len(best_group):
            best_group = group
            best_key = key
    return best_key, best_group


def compute_result_confidence(
    task: str,
    inputs: List[Dict[str, object]],
    group: List[Fact],
) -> float:
    if not inputs:
        return 0.0
    conf_values = [
        float(i.get("confidence", 0.0))
        for i in inputs
        if i.get("confidence") is not None
    ]
    if not conf_values:
        return 0.0
    base_conf = min(conf_values)
    year_bonus = 0.0
    if task == "yoy":
        inferred_flags = [bool(i.get("inferred_year")) for i in inputs]
        if not any(inferred_flags):
            year_bonus += 0.1
        if all(i.get("year") is not None for i in inputs):
            year_bonus += 0.1
    unit_bonus = 0.0
    units = [i.get("unit") for i in inputs]
    if all(u is not None for u in units) and len(set(units)) == 1:
        unit_bonus += 0.1
    metric_bonus = 0.0
    if any(f.metric for f in group):
        metric_bonus += 0.05
    if any(f.entity for f in group):
        metric_bonus += 0.05
    conflict_penalty = 0.0
    if len(group) > len(inputs) + 1:
        conflict_penalty -= 0.1
    score = base_conf + year_bonus + unit_bonus + metric_bonus + conflict_penalty
    return max(0.0, min(1.0, score))


def pick_values_for_years(facts: List[Fact], years: List[int]) -> Optional[List[Fact]]:
    values = []
    for y in years:
        candidates = [f for f in facts if f.year == y]
        if not candidates:
            return None
        candidates.sort(key=lambda x: x.confidence, reverse=True)
        values.append(candidates[0])
    return values


def compute_yoy(
    query: str,
    facts: List[Fact],
    output_percent: bool,
) -> Tuple[CalcResult, CalcTrace]:
    years = [int(m.group(0)) for m in YEAR_RE.finditer(query)]
    years = sorted(list(dict.fromkeys(years)))
    selected = None
    if len(years) >= 2:
        years_use = years[-2:]
        selected = pick_values_for_years(facts, years_use)

    if not selected:
        # Fallback: pick two facts with distinct years by confidence.
        facts_with_year = [f for f in facts if f.year is not None]
        facts_with_year = sorted(facts_with_year, key=lambda x: x.confidence, reverse=True)
        unique = {}
        for f in facts_with_year:
            if f.year not in unique:
                unique[f.year] = f
        if len(unique) >= 2:
            years_sorted = sorted(unique.keys())[-2:]
            selected = [unique[y] for y in years_sorted]

    if not selected:
        return (
            CalcResult(
                qid="",
                task_type="yoy",
                inputs=[],
                result_value=None,
                result_unit="%" if output_percent else "ratio",
                explanation="insufficient facts",
                confidence=0.0,
                status="insufficient_facts",
            ),
            CalcTrace(
                qid="",
                task_type="yoy",
                selected_key=None,
                candidates=len(facts),
                reason="missing_years",
            ),
        )

    selected_by_year = {f.year: f for f in selected if f.year is not None}
    if len(selected_by_year) < 2:
        return (
            CalcResult(
                qid="",
                task_type="yoy",
                inputs=[],
                result_value=None,
                result_unit="%" if output_percent else "ratio",
                explanation="insufficient facts",
                confidence=0.0,
                status="insufficient_facts",
            ),
            CalcTrace(
                qid="",
                task_type="yoy",
                selected_key=None,
                candidates=len(facts),
                reason="missing_years",
            ),
        )

    years_sorted = sorted(selected_by_year.keys())
    x_prev = selected_by_year[years_sorted[0]]
    x_t = selected_by_year[years_sorted[1]]

    if x_prev.unit and x_t.unit and x_prev.unit != x_t.unit:
        return (
            CalcResult(
                qid="",
                task_type="yoy",
                inputs=[],
                result_value=None,
                result_unit="%" if output_percent else "ratio",
                explanation="unit mismatch",
                confidence=0.0,
                status="unit_mismatch",
            ),
            CalcTrace(
                qid="",
                task_type="yoy",
                selected_key=None,
                candidates=len(facts),
                reason="unit_mismatch",
            ),
        )
    if x_prev.value == 0:
        return (
            CalcResult(
                qid="",
                task_type="yoy",
                inputs=[],
                result_value=None,
                result_unit="%" if output_percent else "ratio",
                explanation="division by zero",
                confidence=0.0,
                status="invalid",
            ),
            CalcTrace(
                qid="",
                task_type="yoy",
                selected_key=None,
                candidates=len(facts),
                reason="zero_base",
            ),
        )

    yoy = (x_t.value - x_prev.value) / x_prev.value
    result_value = yoy * 100 if output_percent else yoy
    unit = "%" if output_percent else "ratio"

    explanation = f"YoY = ({x_t.value} - {x_prev.value}) / {x_prev.value}"
    inputs = [
        {
            "year": x_t.year,
            "value": x_t.value,
            "unit": x_t.unit,
            "chunk_id": x_t.chunk_id,
            "inferred_year": x_t.inferred_year,
            "confidence": x_t.confidence,
        },
        {
            "year": x_prev.year,
            "value": x_prev.value,
            "unit": x_prev.unit,
            "chunk_id": x_prev.chunk_id,
            "inferred_year": x_prev.inferred_year,
            "confidence": x_prev.confidence,
        },
    ]
    return (
        CalcResult(
            qid="",
            task_type="yoy",
            inputs=inputs,
            result_value=result_value,
            result_unit=unit,
            explanation=explanation,
            confidence=min(x_t.confidence, x_prev.confidence),
            status="ok",
        ),
        CalcTrace(qid="", task_type="yoy", selected_key=None, candidates=len(facts), reason="ok"),
    )


def compute_diff(facts: List[Fact]) -> Tuple[CalcResult, CalcTrace]:
    if len(facts) < 2:
        return (
            CalcResult(
                qid="",
                task_type="diff",
                inputs=[],
                result_value=None,
                result_unit=None,
                explanation="insufficient facts",
                confidence=0.0,
                status="insufficient_facts",
            ),
            CalcTrace(
                qid="",
                task_type="diff",
                selected_key=None,
                candidates=len(facts),
                reason="too_few",
            ),
        )

    facts_sorted = sorted(facts, key=lambda x: x.confidence, reverse=True)[:2]
    a, b = facts_sorted[0], facts_sorted[1]

    if a.unit != b.unit:
        return (
            CalcResult(
                qid="",
                task_type="diff",
                inputs=[],
                result_value=None,
                result_unit=None,
                explanation="unit mismatch",
                confidence=0.0,
                status="unit_mismatch",
            ),
            CalcTrace(
                qid="",
                task_type="diff",
                selected_key=None,
                candidates=len(facts),
                reason="unit_mismatch",
            ),
        )

    result_value = a.value - b.value
    explanation = f"diff = {a.value} - {b.value}"
    inputs = [
        {
            "year": a.year,
            "value": a.value,
            "unit": a.unit,
            "chunk_id": a.chunk_id,
            "inferred_year": a.inferred_year,
            "confidence": a.confidence,
        },
        {
            "year": b.year,
            "value": b.value,
            "unit": b.unit,
            "chunk_id": b.chunk_id,
            "inferred_year": b.inferred_year,
            "confidence": b.confidence,
        },
    ]

    return (
        CalcResult(
            qid="",
            task_type="diff",
            inputs=inputs,
            result_value=result_value,
            result_unit=a.unit,
            explanation=explanation,
            confidence=min(a.confidence, b.confidence),
            status="ok",
        ),
        CalcTrace(qid="", task_type="diff", selected_key=None, candidates=len(facts), reason="ok"),
    )


def compute_share(facts: List[Fact]) -> Tuple[CalcResult, CalcTrace]:
    if len(facts) < 2:
        return (
            CalcResult(
                qid="",
                task_type="share",
                inputs=[],
                result_value=None,
                result_unit="%",
                explanation="insufficient facts",
                confidence=0.0,
                status="insufficient_facts",
            ),
            CalcTrace(
                qid="",
                task_type="share",
                selected_key=None,
                candidates=len(facts),
                reason="too_few",
            ),
        )

    facts_sorted = sorted(facts, key=lambda x: x.value, reverse=True)
    total, part = facts_sorted[0], facts_sorted[1]
    if total.unit != part.unit:
        return (
            CalcResult(
                qid="",
                task_type="share",
                inputs=[],
                result_value=None,
                result_unit="%",
                explanation="unit mismatch",
                confidence=0.0,
                status="unit_mismatch",
            ),
            CalcTrace(
                qid="",
                task_type="share",
                selected_key=None,
                candidates=len(facts),
                reason="unit_mismatch",
            ),
        )

    share = part.value / total.value if total.value else None
    if share is None:
        return (
            CalcResult(
                qid="",
                task_type="share",
                inputs=[],
                result_value=None,
                result_unit="%",
                explanation="division by zero",
                confidence=0.0,
                status="invalid",
            ),
            CalcTrace(
                qid="",
                task_type="share",
                selected_key=None,
                candidates=len(facts),
                reason="zero_base",
            ),
        )

    result_value = share * 100
    explanation = f"share = {part.value} / {total.value}"
    inputs = [
        {
            "year": part.year,
            "value": part.value,
            "unit": part.unit,
            "chunk_id": part.chunk_id,
            "inferred_year": part.inferred_year,
            "confidence": part.confidence,
        },
        {
            "year": total.year,
            "value": total.value,
            "unit": total.unit,
            "chunk_id": total.chunk_id,
            "inferred_year": total.inferred_year,
            "confidence": total.confidence,
        },
    ]

    return (
        CalcResult(
            qid="",
            task_type="share",
            inputs=inputs,
            result_value=result_value,
            result_unit="%",
            explanation=explanation,
            confidence=min(part.confidence, total.confidence),
            status="ok",
        ),
        CalcTrace(qid="", task_type="share", selected_key=None, candidates=len(facts), reason="ok"),
    )


def compute_multiple(facts: List[Fact]) -> Tuple[CalcResult, CalcTrace]:
    if len(facts) < 2:
        return (
            CalcResult(
                qid="",
                task_type="multiple",
                inputs=[],
                result_value=None,
                result_unit="x",
                explanation="insufficient facts",
                confidence=0.0,
                status="insufficient_facts",
            ),
            CalcTrace(
                qid="",
                task_type="multiple",
                selected_key=None,
                candidates=len(facts),
                reason="too_few",
            ),
        )

    facts_sorted = sorted(facts, key=lambda x: x.confidence, reverse=True)[:2]
    a, b = facts_sorted[0], facts_sorted[1]
    if a.unit != b.unit:
        return (
            CalcResult(
                qid="",
                task_type="multiple",
                inputs=[],
                result_value=None,
                result_unit="x",
                explanation="unit mismatch",
                confidence=0.0,
                status="unit_mismatch",
            ),
            CalcTrace(
                qid="",
                task_type="multiple",
                selected_key=None,
                candidates=len(facts),
                reason="unit_mismatch",
            ),
        )

    if b.value == 0:
        return (
            CalcResult(
                qid="",
                task_type="multiple",
                inputs=[],
                result_value=None,
                result_unit="x",
                explanation="division by zero",
                confidence=0.0,
                status="invalid",
            ),
            CalcTrace(
                qid="",
                task_type="multiple",
                selected_key=None,
                candidates=len(facts),
                reason="zero_base",
            ),
        )

    result_value = a.value / b.value
    explanation = f"multiple = {a.value} / {b.value}"
    inputs = [
        {
            "year": a.year,
            "value": a.value,
            "unit": a.unit,
            "chunk_id": a.chunk_id,
            "inferred_year": a.inferred_year,
            "confidence": a.confidence,
        },
        {
            "year": b.year,
            "value": b.value,
            "unit": b.unit,
            "chunk_id": b.chunk_id,
            "inferred_year": b.inferred_year,
            "confidence": b.confidence,
        },
    ]

    return (
        CalcResult(
            qid="",
            task_type="multiple",
            inputs=inputs,
            result_value=result_value,
            result_unit="x",
            explanation=explanation,
            confidence=min(a.confidence, b.confidence),
            status="ok",
        ),
        CalcTrace(
            qid="",
            task_type="multiple",
            selected_key=None,
            candidates=len(facts),
            reason="ok",
        ),
    )


def _attach_parser(trace: CalcTrace, parsed: TaskParseResult) -> None:
    trace.parser_mode = parsed.mode
    trace.parser_confidence = parsed.confidence
    trace.parser_rule = parsed.rule
    trace.parser_rejected = parsed.rejected
    trace.parser_scores = dict(parsed.scores)
    trace.parser_rules = list(parsed.rules)


def compute_for_query(
    query: str,
    facts: List[Fact],
    output_percent: bool = True,
    task_parser_mode: str = "v1",
    task_parser_min_conf: float = 0.0,
) -> Tuple[CalcResult, CalcTrace]:
    parsed = parse_task(query, mode=task_parser_mode, min_conf=task_parser_min_conf)
    task = parsed.task_type
    if not task:
        trace = CalcTrace(
            qid="",
            task_type="unknown",
            selected_key=None,
            candidates=len(facts),
            reason="no_task",
        )
        _attach_parser(trace, parsed)
        return (
            CalcResult(
                qid="",
                task_type="unknown",
                inputs=[],
                result_value=None,
                result_unit=None,
                explanation="no task match",
                confidence=0.0,
                status="no_match",
            ),
            trace,
        )

    groups = group_facts(facts)
    key, group = select_group(groups)
    if not group:
        trace = CalcTrace(
            qid="",
            task_type=task,
            selected_key=None,
            candidates=0,
            reason="no_facts",
        )
        _attach_parser(trace, parsed)
        return (
            CalcResult(
                qid="",
                task_type=task,
                inputs=[],
                result_value=None,
                result_unit=None,
                explanation="no facts",
                confidence=0.0,
                status="no_match",
            ),
            trace,
        )

    # Basic ambiguity check for non-year tasks.
    if task in {"diff", "share", "multiple"}:
        year_values = {f.year for f in group if f.year is not None}
        if not year_values and len(group) > 2:
            result = CalcResult(
                qid="",
                task_type=task,
                inputs=[],
                result_value=None,
                result_unit=None,
                explanation="ambiguous multiple candidates",
                confidence=0.0,
                status="ambiguous",
            )
            trace = CalcTrace(
                qid="",
                task_type=task,
                selected_key=key,
                candidates=len(group),
                reason="ambiguous",
            )
            _attach_parser(trace, parsed)
            return result, trace

    if task == "yoy":
        result, trace = compute_yoy(query, group, output_percent)
    elif task == "diff":
        result, trace = compute_diff(group)
    elif task == "share":
        result, trace = compute_share(group)
    elif task == "multiple":
        result, trace = compute_multiple(group)
    else:
        result = CalcResult(
            qid="",
            task_type=task,
            inputs=[],
            result_value=None,
            result_unit=None,
            explanation="unsupported",
            confidence=0.0,
            status="no_match",
        )
        trace = CalcTrace(
            qid="",
            task_type=task,
            selected_key=None,
            candidates=len(facts),
            reason="unsupported",
        )

    if result.status == "ok":
        result.confidence = compute_result_confidence(task, result.inputs, group)
    else:
        result.confidence = 0.0

    result.qid = ""
    trace.qid = ""
    trace.selected_key = key
    _attach_parser(trace, parsed)
    return result, trace
