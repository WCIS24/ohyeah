from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from calculator.extract import Fact

YOY_KW = [
    "yoy",
    "year over year",
    "growth",
    "increase",
    "decrease",
    "同比",
    "增速",
    "增长率",
    "增长",
    "下降",
]
DIFF_KW = ["difference", "change", "delta", "diff", "差值", "变化", "增减", "差异"]
SHARE_KW = ["share", "percentage", "portion", "占比", "比例", "份额"]
MULT_KW = ["times", "multiple", "倍", "倍数"]

YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


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


def detect_task(query: str) -> Optional[str]:
    q = query.lower()
    if any(k in q for k in YOY_KW):
        return "yoy"
    if any(k in q for k in DIFF_KW):
        return "diff"
    if any(k in q for k in SHARE_KW):
        return "share"
    if any(k in q for k in MULT_KW):
        return "multiple"
    return None


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
        # fallback: pick two facts with distinct years by confidence
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
        {"year": x_t.year, "value": x_t.value, "unit": x_t.unit, "chunk_id": x_t.chunk_id},
        {
            "year": x_prev.year,
            "value": x_prev.value,
            "unit": x_prev.unit,
            "chunk_id": x_prev.chunk_id,
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
        {"year": a.year, "value": a.value, "unit": a.unit, "chunk_id": a.chunk_id},
        {"year": b.year, "value": b.value, "unit": b.unit, "chunk_id": b.chunk_id},
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
        {"year": part.year, "value": part.value, "unit": part.unit, "chunk_id": part.chunk_id},
        {"year": total.year, "value": total.value, "unit": total.unit, "chunk_id": total.chunk_id},
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
        {"year": a.year, "value": a.value, "unit": a.unit, "chunk_id": a.chunk_id},
        {"year": b.year, "value": b.value, "unit": b.unit, "chunk_id": b.chunk_id},
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


def compute_for_query(
    query: str,
    facts: List[Fact],
    output_percent: bool = True,
) -> Tuple[CalcResult, CalcTrace]:
    task = detect_task(query)
    if not task:
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
            CalcTrace(
                qid="",
                task_type="unknown",
                selected_key=None,
                candidates=len(facts),
                reason="no_task",
            ),
        )

    groups = group_facts(facts)
    key, group = select_group(groups)
    if not group:
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
            CalcTrace(qid="", task_type=task, selected_key=None, candidates=0, reason="no_facts"),
        )

    # basic ambiguity check for non-year tasks
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

    result.qid = ""
    trace.qid = ""
    trace.selected_key = key
    return result, trace
