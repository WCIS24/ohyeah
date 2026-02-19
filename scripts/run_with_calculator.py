from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from calculator.compute import (  # noqa: E402
    CalcResult,
    CalcTrace,
    compute_for_query,
    group_facts,
    parse_task_with_lookup,
    select_group,
)
from calculator.extract import Fact, extract_facts_from_text  # noqa: E402
from config.schema import get_path, resolve_config, validate_config, validate_paths  # noqa: E402
from config.schema import write_resolved_config  # noqa: E402
from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402
from retrieval.query_expansion import build_query_expander_from_config  # noqa: E402
from retrieval.retriever import HybridRetriever  # noqa: E402
from training.pairs import load_jsonl  # noqa: E402

YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
ENTITY_RE = re.compile(r"\b[A-Z]{2,6}\b")
PERCENT_HINT_RE = re.compile(r"%|percent|percentage|\u767e\u5206", re.IGNORECASE)
CURRENCY_HINT_RE = re.compile(r"\$|usd|us\$|eur|cny|rmb|hkd", re.IGNORECASE)

TASK_KEYWORDS: Dict[str, List[str]] = {
    "yoy": [
        "yoy",
        "year over year",
        "growth",
        "increase",
        "decrease",
        "rate",
        "\u540c\u6bd4",
        "\u73af\u6bd4",
        "\u589e\u901f",
        "\u589e\u957f\u7387",
        "\u53d8\u5316\u7387",
    ],
    "diff": [
        "difference",
        "diff",
        "delta",
        "change",
        "from",
        "to",
        "\u589e\u52a0",
        "\u51cf\u5c11",
        "\u5dee\u503c",
        "\u5dee\u989d",
    ],
    "share": ["share", "portion", "percentage", "ratio", "\u5360\u6bd4", "\u6bd4\u4f8b"],
    "multiple": ["times", "multiple", "how many times", "\u500d", "\u591a\u5c11\u500d"],
}

VALID_FACT_SELECTOR_MODES = {"legacy", "legacy_largest_group", "scored_v1"}
VALID_TASK_PARSER_MODES = {"v1", "v2"}
PERCENT_UNITS = {"%", "percent", "percentage", "pct", "bp", "bps", "百分点"}
METRIC_HINTS = [
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run retrieval + calculator pipeline")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--subset-qids", default=None, help="Optional subset qid list")
    parser.add_argument("--use-multistep", type=int, default=None, help="1/0 override")
    parser.add_argument("--multistep-results", default=None, help="Override multistep results path")
    return parser.parse_args()


def apply_overrides(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    if args.subset_qids is not None:
        config["subset_qids_path"] = args.subset_qids
    if args.use_multistep is not None:
        config["use_multistep_results"] = bool(args.use_multistep)
    if args.multistep_results is not None:
        config["multistep_results_path"] = args.multistep_results
    return config


def load_subset(path: Optional[str]) -> Optional[set[str]]:
    if not path:
        return None
    qids = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            qid = line.strip()
            if qid:
                qids.add(qid)
    return qids


def placeholder_generate(query: str, chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return "No evidence found."
    snippet = chunks[0].get("text", "").replace("\n", " ").strip()
    return f"Q: {query}\nAnswer (template): {snippet[:200]}"


def baseline_answer_generate(chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return "No evidence found."
    snippet = chunks[0].get("text", "").replace("\n", " ").strip()
    if not snippet:
        return "No evidence found."
    return f"Answer based on evidence: {snippet[:220]}"


def _keyword_hits(query: str, keywords: List[str]) -> List[str]:
    q_lower = (query or "").lower()
    hits: List[str] = []
    for kw in keywords:
        if not kw:
            continue
        if kw.lower() in q_lower:
            hits.append(kw)
    return hits


def selective_pre_gate(
    query: str,
    *,
    pre_gate_cfg: Dict[str, Any],
    enable_lookup: bool,
) -> Dict[str, Any]:
    tau_need = float(pre_gate_cfg.get("tau_need", 0.8))
    positive_keywords = [str(x) for x in pre_gate_cfg.get("positive_keywords", [])]
    negative_keywords = [str(x) for x in pre_gate_cfg.get("negative_keywords", [])]
    negative_enabled = bool(get_path(pre_gate_cfg, "negative_intent.enabled", True))

    parser_probe = parse_task_with_lookup(
        query,
        mode="v2",
        min_conf=0.0,
        enable_lookup=enable_lookup,
    )
    positive_hits = _keyword_hits(query, positive_keywords)
    negative_hits = _keyword_hits(query, negative_keywords)
    parser_pass = (
        parser_probe.task_type is not None and float(parser_probe.confidence) >= float(tau_need)
    )

    if negative_enabled and negative_hits and not positive_hits:
        return {
            "needs_calc": False,
            "task_type": parser_probe.task_type,
            "conf": float(parser_probe.confidence),
            "skip_reason": "negative_intent",
            "positive_hits": positive_hits,
            "negative_hits": negative_hits,
            "parser_rule": parser_probe.rule,
        }

    if positive_hits or parser_pass:
        task_type = parser_probe.task_type
        if task_type is None and enable_lookup and positive_hits:
            task_type = "lookup"
        return {
            "needs_calc": True,
            "task_type": task_type,
            "conf": float(parser_probe.confidence),
            "skip_reason": None,
            "positive_hits": positive_hits,
            "negative_hits": negative_hits,
            "parser_rule": parser_probe.rule,
        }

    return {
        "needs_calc": False,
        "task_type": parser_probe.task_type,
        "conf": float(parser_probe.confidence),
        "skip_reason": "no_numeric_intent",
        "positive_hits": positive_hits,
        "negative_hits": negative_hits,
        "parser_rule": parser_probe.rule,
    }


def _normalize_unit(unit: Optional[str]) -> Optional[str]:
    if unit is None:
        return None
    raw = str(unit).strip().lower()
    if raw in {"%", "percent", "percentage", "pct"}:
        return "%"
    if raw in {"bp", "bps", "basis point", "basis points"}:
        return "bps"
    return raw


def _units_consistent(facts: List[Fact]) -> bool:
    units = [_normalize_unit(f.unit) for f in facts if f.unit]
    return len(set(units)) <= 1


def _top_k_by_conf(facts: List[Fact], k: int) -> List[Fact]:
    k_use = max(1, int(k))
    return sorted(facts, key=lambda x: float(x.confidence), reverse=True)[:k_use]


def selective_evidence_gate(
    query: str,
    *,
    task_type: Optional[str],
    facts: List[Fact],
    evidence_cfg: Dict[str, Any],
    lookup_cfg: Dict[str, Any],
) -> Tuple[bool, str, List[Fact]]:
    if not task_type:
        return False, "insufficient_operands_precheck", []

    strict_year = bool(evidence_cfg.get("strict_year", True))
    require_unit = bool(evidence_cfg.get("require_unit_consistency", True))
    min_ops = evidence_cfg.get("min_operands", {}) or {}
    min_default = 2
    min_operands = int(min_ops.get(task_type, 1 if task_type == "lookup" else min_default))

    filtered = list(facts)
    if strict_year:
        filtered = [f for f in filtered if not bool(f.inferred_year)]
    if len(filtered) < min_operands:
        return False, "insufficient_operands_precheck", []

    if task_type == "yoy":
        yoy_facts = [f for f in filtered if f.year is not None]
        if len(yoy_facts) < min_operands:
            return False, "year_missing_precheck", []
        years = sorted({int(f.year) for f in yoy_facts if f.year is not None})
        if len(years) < 2:
            return False, "year_missing_precheck", []
        groups: Dict[Tuple[Optional[str], Optional[str], Optional[str]], List[Fact]] = {}
        for fact in yoy_facts:
            groups.setdefault((fact.metric, fact.entity, fact.unit), []).append(fact)
        ranked = sorted(
            groups.values(),
            key=lambda rows: (len(rows), max(float(f.confidence) for f in rows)),
            reverse=True,
        )
        best_group = ranked[0] if ranked else yoy_facts
        if len({f.year for f in best_group if f.year is not None}) < 2:
            return False, "insufficient_operands_precheck", []
        if require_unit and not _units_consistent(best_group):
            return False, "unit_mismatch_precheck", []
        picked_by_year: Dict[int, Fact] = {}
        for fact in _top_k_by_conf(best_group, len(best_group)):
            if fact.year is None:
                continue
            picked_by_year.setdefault(int(fact.year), fact)
        years_use = sorted(picked_by_year.keys())[-2:]
        selected = [picked_by_year[y] for y in years_use]
        if len(selected) < 2:
            return False, "year_missing_precheck", []
        return True, "ok", selected

    if task_type in {"diff", "multiple", "share"}:
        selected = _top_k_by_conf(filtered, max(min_operands, 2))
        if len(selected) < min_operands:
            return False, "insufficient_operands_precheck", []
        if require_unit and not _units_consistent(selected):
            return False, "unit_mismatch_precheck", []
        if task_type == "share":
            denom = max(float(f.value) for f in selected)
            if abs(denom) < 1e-12:
                return False, "denom_missing_precheck", []
        return True, "ok", selected

    if task_type == "lookup":
        constraints = build_constraints(query)
        years = constraints.get("years", [])
        require_explicit_year = bool(lookup_cfg.get("require_explicit_year", True))
        if strict_year and require_explicit_year and not years:
            return False, "year_missing_precheck", []
        lookup_facts = list(filtered)
        if years:
            lookup_facts = [f for f in lookup_facts if f.year in years]
            if not lookup_facts:
                return False, "year_missing_precheck", []
        metric_terms = [m for m in METRIC_HINTS if m in (query or "").lower()]
        if metric_terms:
            metric_filtered = [
                f
                for f in lookup_facts
                if f.metric and str(f.metric).lower() in set(metric_terms)
            ]
            if metric_filtered:
                lookup_facts = metric_filtered
        if not lookup_facts:
            return False, "insufficient_operands_precheck", []
        selected = _top_k_by_conf(lookup_facts, 1)
        return True, "ok", selected

    return False, "insufficient_operands_precheck", []


def selective_post_gate(result: CalcResult, post_cfg: Dict[str, Any]) -> Tuple[bool, str]:
    if not bool(post_cfg.get("enabled", True)):
        return True, "ok"
    if result.status != "ok":
        return False, f"status_{result.status}"

    if bool(post_cfg.get("require_unit_ok", True)):
        units = [_normalize_unit(i.get("unit")) for i in result.inputs if i.get("unit")]
        if len(set(units)) > 1:
            return False, "unit_mismatch_postcheck"

    if result.task_type == "share":
        value = result.result_value
        if value is None:
            return False, "share_missing_value"
        share_range = post_cfg.get("share_range", [0.0, 100.0]) or [0.0, 100.0]
        lo = float(share_range[0]) if len(share_range) >= 1 else 0.0
        hi = float(share_range[1]) if len(share_range) >= 2 else 100.0
        unit = _normalize_unit(result.result_unit)
        if unit not in {"%", "bps"}:
            lo, hi = 0.0, 1.0
        if float(value) < lo or float(value) > hi:
            return False, "share_out_of_range_postcheck"

    if result.task_type == "yoy":
        value = result.result_value
        if value is None:
            return False, "yoy_missing_value"
        yoy_abs_max = float(post_cfg.get("yoy_abs_max", 1000.0))
        if abs(float(value)) > yoy_abs_max:
            return False, "yoy_out_of_range_postcheck"

    return True, "ok"


def _attach_parser_fields(trace: CalcTrace, parsed: Any) -> None:
    trace.parser_mode = parsed.mode
    trace.parser_confidence = parsed.confidence
    trace.parser_rule = parsed.rule
    trace.parser_rejected = parsed.rejected
    trace.parser_scores = dict(parsed.scores)
    trace.parser_rules = list(parsed.rules)


def build_skip_result(
    *,
    qid: str,
    task_type: Optional[str],
    reason: str,
    parsed: Any,
) -> Tuple[CalcResult, CalcTrace]:
    task = task_type or "unknown"
    result = CalcResult(
        qid=qid,
        task_type=task,
        inputs=[],
        result_value=None,
        result_unit=None,
        explanation=f"skipped: {reason}",
        confidence=0.0,
        status="skipped",
    )
    trace = CalcTrace(
        qid=qid,
        task_type=task,
        selected_key=None,
        candidates=0,
        reason=f"skipped:{reason}",
    )
    _attach_parser_fields(trace, parsed)
    return result, trace


def build_retriever(config: Dict[str, Any]) -> HybridRetriever:
    retriever_cfg = config.get("retriever", {})
    retriever = HybridRetriever(
        model_name=get_path(config, "retriever.dense.model_name_or_path"),
        use_faiss=bool(get_path(config, "retriever.index.use_faiss", False)),
        device=retriever_cfg.get("device"),
        batch_size=int(retriever_cfg.get("batch_size", 32)),
    )
    corpus_dir = get_path(config, "data.corpus_dir", "data/corpus")
    corpus_file = get_path(config, "data.corpus_file", "chunks.jsonl")
    corpus_path = os.path.join(corpus_dir, corpus_file)
    corpus_chunks = load_jsonl(corpus_path)
    retriever.build_index(corpus_chunks)
    expander = build_query_expander_from_config(config)
    if expander is not None:
        qexpand_cfg = get_path(config, "qexpand", {}) or {}
        retriever.set_query_expander(expander, qexpand_cfg if isinstance(qexpand_cfg, dict) else {})
    return retriever


def build_constraints(query: str) -> Dict[str, Any]:
    years = sorted({int(m.group(0)) for m in YEAR_RE.finditer(query or "")})
    entity = None
    match = ENTITY_RE.search(query or "")
    if match is not None:
        entity = match.group(0).upper()
    return {
        "years": years,
        "entity": entity,
        "expect_percent": bool(PERCENT_HINT_RE.search(query or "")),
        "expect_currency": bool(CURRENCY_HINT_RE.search(query or "")),
    }


def chunk_maps(chunks: List[Dict[str, Any]]) -> Tuple[Dict[str, int], Dict[str, str]]:
    ranks: Dict[str, int] = {}
    texts: Dict[str, str] = {}
    for idx, chunk in enumerate(chunks, start=1):
        chunk_id = chunk.get("chunk_id") or chunk.get("meta", {}).get("chunk_id")
        if chunk_id:
            key = str(chunk_id)
            ranks[key] = idx
            texts[key] = str(chunk.get("text", ""))
    return ranks, texts


def score_fact(
    fact: Fact,
    *,
    query: str,
    task_hint: Optional[str],
    constraints: Dict[str, Any],
    rank_map: Dict[str, int],
    text_map: Dict[str, str],
    weights: Dict[str, float],
) -> Dict[str, Any]:
    q_lower = (query or "").lower()
    raw_lower = (fact.raw_span or "").lower()
    rank = int(rank_map.get(str(fact.chunk_id), len(rank_map) + 10))
    f_rank = 1.0 / max(rank, 1)
    f_year = 1.0 if constraints["years"] and fact.year in constraints["years"] else 0.0
    if constraints["expect_percent"]:
        f_unit = 1.0 if fact.unit == "%" else 0.0
    elif constraints["expect_currency"]:
        f_unit = 1.0 if fact.unit == "USD" else 0.0
    else:
        f_unit = 0.25 if fact.unit is not None else 0.0
    f_entity = 0.0
    entity = constraints["entity"]
    if entity:
        if entity in text_map.get(str(fact.chunk_id), "").upper():
            f_entity = 1.0
        elif fact.entity and str(fact.entity).upper() == entity:
            f_entity = 0.7
    f_keyword = 0.0
    metric = (fact.metric or "").lower()
    if metric and metric in q_lower:
        f_keyword += 0.5
    if task_hint:
        kws = TASK_KEYWORDS.get(task_hint, [])
        if kws and any(k in q_lower for k in kws):
            if any(k in raw_lower for k in kws):
                f_keyword += 0.35
        if task_hint in {"yoy", "diff"} and fact.year is not None:
            f_keyword += 0.2
        if task_hint in {"share", "multiple"} and fact.unit is not None:
            f_keyword += 0.1
    f_keyword = min(1.0, f_keyword)
    components = {
        "rank": weights["w_rank"] * f_rank,
        "year": weights["w_year"] * f_year,
        "unit": weights["w_unit"] * f_unit,
        "entity": weights["w_entity"] * f_entity,
        "keyword": weights["w_keyword"] * f_keyword,
    }
    return {
        "fact": fact,
        "rank": rank,
        "score_total": sum(components.values()),
        "score_components": components,
    }


def score_pair(a: Dict[str, Any], b: Dict[str, Any], task_hint: Optional[str]) -> Dict[str, Any]:
    fa: Fact = a["fact"]
    fb: Fact = b["fact"]
    same_chunk = 1.0 if fa.chunk_id == fb.chunk_id else 0.0
    near_chunk = 1.0 if abs(int(a["rank"]) - int(b["rank"])) <= 1 else 0.0
    same_unit = 1.0 if fa.unit and fb.unit and fa.unit == fb.unit else 0.0
    same_metric = 1.0 if fa.metric and fb.metric and fa.metric == fb.metric else 0.0
    distinct_year = 1.0 if fa.year and fb.year and fa.year != fb.year else 0.0
    task_bonus = 0.0
    if task_hint == "yoy":
        task_bonus += 0.25 * distinct_year + 0.10 * same_unit
    elif task_hint == "diff":
        task_bonus += 0.15 * same_unit + 0.10 * distinct_year
    elif task_hint in {"share", "multiple"}:
        task_bonus += 0.20 * same_unit
    pair_bonus = 0.20 * same_chunk + 0.10 * near_chunk + 0.15 * same_unit + 0.10 * same_metric
    pair_bonus += task_bonus
    return {
        "a": a,
        "b": b,
        "pair_bonus": pair_bonus,
        "score_total": float(a["score_total"]) + float(b["score_total"]) + pair_bonus,
    }


def compact_fact(row: Dict[str, Any]) -> Dict[str, Any]:
    fact: Fact = row["fact"]
    return {
        "chunk_id": fact.chunk_id,
        "year": fact.year,
        "value": fact.value,
        "unit": fact.unit,
        "metric": fact.metric,
        "rank": row["rank"],
        "score_total": row["score_total"],
        "score_components": row["score_components"],
    }


def compact_pair(row: Dict[str, Any]) -> Dict[str, Any]:
    a = row["a"]
    b = row["b"]
    return {
        "score_total": row["score_total"],
        "pair_bonus": row["pair_bonus"],
        "facts": [compact_fact(a), compact_fact(b)],
    }


def _parse_optional_positive_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed


def select_legacy(facts: List[Fact]) -> Tuple[List[Fact], Dict[str, Any]]:
    if not facts:
        return [], {
            "mode": "legacy_largest_group",
            "reason": "no_facts",
            "selected_fact_count": 0,
            "selected_pair_count": 0,
            "selected_chunk_ids": [],
            "selected_numbers": [],
        }
    groups = group_facts(facts)
    key, group = select_group(groups)
    selected = list(group) if group else list(facts)
    return selected, {
        "mode": "legacy_largest_group",
        "reason": "ok",
        "selected_group_key": list(key) if key is not None else None,
        "selected_fact_count": len(selected),
        "selected_pair_count": 0,
        "selected_chunk_ids": [str(f.chunk_id) for f in selected if f.chunk_id][:8],
        "selected_numbers": [float(f.value) for f in selected[:8]],
    }


def select_scored(
    *,
    query: str,
    facts: List[Fact],
    chunks: List[Dict[str, Any]],
    task_hint: Optional[str],
    scored_cfg: Dict[str, Any],
) -> Tuple[List[Fact], Dict[str, Any]]:
    if not facts:
        return [], {
            "mode": "scored_v1",
            "reason": "no_facts",
            "selected_fact_count": 0,
            "selected_pair_count": 0,
            "selected_chunk_ids": [],
            "selected_numbers": [],
            "top_fact_scores": [],
            "selected_pairs": [],
        }
    constraints = build_constraints(query)
    rank_map, text_map = chunk_maps(chunks)
    weights = {
        "w_rank": float(scored_cfg.get("w_rank", 1.0)),
        "w_year": float(scored_cfg.get("w_year", 0.8)),
        "w_unit": float(scored_cfg.get("w_unit", 0.6)),
        "w_entity": float(scored_cfg.get("w_entity", 0.4)),
        "w_keyword": float(scored_cfg.get("w_keyword", 0.6)),
    }
    top_pairs = max(1, int(scored_cfg.get("top_pairs", 1)))
    top_groups = _parse_optional_positive_int(scored_cfg.get("top_groups"))
    scored = [
        score_fact(
            fact,
            query=query,
            task_hint=task_hint,
            constraints=constraints,
            rank_map=rank_map,
            text_map=text_map,
            weights=weights,
        )
        for fact in facts
    ]
    scored.sort(key=lambda x: (float(x["score_total"]), float(x["fact"].confidence)), reverse=True)

    chosen_group_keys: List[List[Any]] = []
    group_scores_top: List[Dict[str, Any]] = []
    if top_groups is not None:
        grouped_rows: Dict[
            Tuple[Optional[str], Optional[str], Optional[str]],
            List[Dict[str, Any]],
        ] = {}
        for row in scored:
            fact = row["fact"]
            gkey = (fact.metric, fact.entity, fact.unit)
            grouped_rows.setdefault(gkey, []).append(row)
        ranked_groups: List[Tuple[float, Tuple[Optional[str], Optional[str], Optional[str]]]] = []
        for gkey, rows in grouped_rows.items():
            max_score = max(float(r["score_total"]) for r in rows)
            year_cov = len({r["fact"].year for r in rows if r["fact"].year is not None})
            ranked_score = max_score + 0.20 * len(rows) + 0.10 * year_cov
            ranked_groups.append((ranked_score, gkey))
        ranked_groups.sort(key=lambda x: x[0], reverse=True)
        selected_gkeys = {k for _s, k in ranked_groups[:top_groups]}
        chosen_group_keys = [[k[0], k[1], k[2]] for k in selected_gkeys]
        group_scores_top = [
            {"group_key": [k[0], k[1], k[2]], "score": float(s)}
            for s, k in ranked_groups[: min(5, len(ranked_groups))]
        ]
        filtered = [
            row
            for row in scored
            if (row["fact"].metric, row["fact"].entity, row["fact"].unit) in selected_gkeys
        ]
        candidate = (
            filtered[: min(24, len(filtered))]
            if filtered
            else scored[: min(24, len(scored))]
        )
    else:
        candidate = scored[: min(24, len(scored))]

    pairs = []
    for i in range(len(candidate)):
        for j in range(i + 1, len(candidate)):
            pairs.append(score_pair(candidate[i], candidate[j], task_hint))
    pairs.sort(key=lambda x: float(x["score_total"]), reverse=True)
    chosen_pairs = pairs[:top_pairs] if pairs else []
    seen = set()
    selected: List[Fact] = []
    for pair in chosen_pairs:
        for side in ("a", "b"):
            fact = pair[side]["fact"]
            key = (str(fact.chunk_id), fact.year, float(fact.value), fact.unit, fact.metric)
            if key in seen:
                continue
            seen.add(key)
            selected.append(fact)
    # Keep a small scored pool for computation so the selector does not
    # over-prune and trigger "insufficient_facts" too aggressively.
    keep_facts = max(4, 2 * top_pairs + 2)
    for row in scored:
        if len(selected) >= keep_facts:
            break
        fact = row["fact"]
        key = (str(fact.chunk_id), fact.year, float(fact.value), fact.unit, fact.metric)
        if key in seen:
            continue
        seen.add(key)
        selected.append(fact)
    if not selected:
        selected = [candidate[0]["fact"]]
    selected.sort(key=lambda f: rank_map.get(str(f.chunk_id), 10_000))
    return selected, {
        "mode": "scored_v1",
        "reason": "ok" if pairs else "single_fact_only",
        "task_hint": task_hint,
        "query_constraints": constraints,
        "weights": weights,
        "top_groups": top_groups,
        "selected_group_keys": chosen_group_keys,
        "group_scores_top": group_scores_top,
        "selected_fact_count": len(selected),
        "selected_pair_count": len(chosen_pairs),
        "selected_chunk_ids": [str(f.chunk_id) for f in selected if f.chunk_id],
        "selected_numbers": [float(f.value) for f in selected],
        "top_fact_scores": [compact_fact(x) for x in scored[:5]],
        "selected_pairs": [compact_pair(x) for x in chosen_pairs],
    }


def select_facts(
    *,
    query: str,
    facts: List[Fact],
    chunks: List[Dict[str, Any]],
    mode: str,
    scored_cfg: Dict[str, Any],
    task_hint: Optional[str],
) -> Tuple[List[Fact], Dict[str, Any]]:
    if mode == "scored_v1":
        return select_scored(
            query=query,
            facts=facts,
            chunks=chunks,
            task_hint=task_hint,
            scored_cfg=scored_cfg,
        )
    return select_legacy(facts)


def main() -> int:
    args = parse_args()
    raw_config = load_config(args.config)
    raw_config = apply_overrides(raw_config, args)

    run_id = raw_config.get("run_id") or generate_run_id()
    raw_config["run_id"] = run_id
    output_dir = raw_config.get("output_dir", "outputs")
    run_dir = os.path.join(output_dir, run_id)
    ensure_dir(run_dir)

    log_path = os.path.join(run_dir, "logs.txt")
    logger = setup_logging(log_path)
    logger.info("command_line=%s", " ".join(sys.argv))
    logger.info("config_path=%s", args.config)

    git_hash = get_git_hash()
    raw_config["git_hash"] = git_hash
    logger.info("git_hash=%s", git_hash)

    resolved = resolve_config(raw_config)
    resolved_path = write_resolved_config(resolved, run_dir)
    issues = validate_config(resolved) + validate_paths(resolved)
    logger.info("resolved_config_path=%s", resolved_path)
    if issues:
        logger.info("config_issues=%s", issues)

    seed = int(get_path(resolved, "runtime.seed", 42))
    random.seed(seed)
    np.random.seed(seed)
    logger.info("seed=%d", seed)

    processed_dir = get_path(resolved, "data.processed_dir", "data/processed")
    dev_file = get_path(resolved, "data.splits.dev", "dev.jsonl")
    records = load_jsonl(os.path.join(processed_dir, dev_file))
    subset_qids = load_subset(raw_config.get("subset_qids_path"))
    if subset_qids:
        records = [r for r in records if r.get("qid") in subset_qids]

    use_multistep = bool(raw_config.get("use_multistep_results", False))
    multistep_path = raw_config.get("multistep_results_path")
    retriever = None
    if not use_multistep:
        retriever = build_retriever(resolved)
        logger.info("dense_model_loaded=%s", retriever.loaded_model_name)

    retrieval_results = {}
    if use_multistep:
        if not multistep_path or not os.path.exists(multistep_path):
            logger.error("missing multistep_results_path: %s", multistep_path)
            return 2
        for row in load_jsonl(multistep_path):
            qid = row.get("qid")
            if qid:
                retrieval_results[qid] = row

    output_percent = bool(get_path(resolved, "calculator.parsing.output_percent", True))
    top_k = int(get_path(resolved, "retriever.top_k", 5))
    alpha = float(get_path(resolved, "retriever.hybrid.alpha", 0.5))
    mode = get_path(resolved, "retriever.mode", "dense")
    enable_lookup = bool(get_path(resolved, "calculator.tasks.enable_lookup", False))

    selective_cfg = get_path(resolved, "calculator.selective", {}) or {}
    selective_enabled = bool(selective_cfg.get("enabled", False))
    pre_gate_cfg = selective_cfg.get("pre_gate", {}) or {}
    evidence_gate_cfg = selective_cfg.get("evidence_gate", {}) or {}
    post_gate_cfg = selective_cfg.get("post_gate", {}) or {}
    lookup_gate_cfg = selective_cfg.get("lookup", {}) or {}
    selective_pre_gate_enabled = bool(
        pre_gate_cfg.get("enabled", True if selective_enabled else False)
    )
    selective_evidence_gate_enabled = bool(evidence_gate_cfg.get("enabled", True))
    selective_post_gate_enabled = bool(post_gate_cfg.get("enabled", True))

    task_parser_mode = str(get_path(resolved, "calculator.task_parser.mode", "v1")).lower().strip()
    if task_parser_mode not in VALID_TASK_PARSER_MODES:
        logger.warning("invalid calculator.task_parser.mode=%s fallback=v1", task_parser_mode)
        task_parser_mode = "v1"
    task_parser_min_conf = float(get_path(resolved, "calculator.task_parser.v2.min_conf", 0.45))

    selector_mode_override = get_path(resolved, "calculator.selector.mode", None)
    if selector_mode_override is None:
        fact_selector_mode = str(
            get_path(resolved, "calculator.fact_selector.mode", "legacy_largest_group")
        ).lower().strip()
    else:
        fact_selector_mode = str(selector_mode_override).lower().strip()
    if fact_selector_mode == "legacy":
        fact_selector_mode = "legacy_largest_group"
    if fact_selector_mode not in VALID_FACT_SELECTOR_MODES:
        logger.warning("invalid calculator selector mode=%s fallback=legacy", fact_selector_mode)
        fact_selector_mode = "legacy_largest_group"
    fact_selector_scored = get_path(resolved, "calculator.fact_selector.scored_v1", {}) or {}
    selector_soft_fallback = bool(get_path(resolved, "calculator.selector.soft_fallback", False))
    selector_top_groups = _parse_optional_positive_int(
        get_path(resolved, "calculator.selector.top_groups", None)
    )
    execution_top_pairs = _parse_optional_positive_int(
        get_path(resolved, "calculator.execution.top_pairs", None)
    )
    if selector_top_groups is not None:
        fact_selector_scored["top_groups"] = selector_top_groups
    if execution_top_pairs is not None:
        fact_selector_scored["top_pairs"] = execution_top_pairs
    selector_top_pairs = max(1, int(fact_selector_scored.get("top_pairs", 1)))

    max_chunks_raw = get_path(resolved, "calculator.evidence.max_chunks_for_facts", None)
    if max_chunks_raw is None:
        max_chunks = None
    else:
        try:
            max_chunks = int(max_chunks_raw)
        except (TypeError, ValueError):
            max_chunks = None
        if max_chunks is not None and max_chunks <= 0:
            max_chunks = None

    logger.info(
        "retriever_mode=%s top_k=%d alpha=%.3f output_percent=%s",
        mode,
        top_k,
        alpha,
        output_percent,
    )
    logger.info(
        "task_parser mode=%s min_conf=%.3f fact_selector mode=%s lookup=%s",
        task_parser_mode,
        task_parser_min_conf,
        fact_selector_mode,
        enable_lookup,
    )
    logger.info("fact_selector_scored_v1=%s", fact_selector_scored)
    logger.info(
        "selector_soft_fallback=%s selector_top_groups=%s execution_top_pairs=%d",
        selector_soft_fallback,
        selector_top_groups,
        selector_top_pairs,
    )
    logger.info(
        "selective enabled=%s pre_gate=%s evidence_gate=%s post_gate=%s",
        selective_enabled,
        selective_pre_gate_enabled,
        selective_evidence_gate_enabled,
        selective_post_gate_enabled,
    )
    logger.info("calculator_max_chunks_for_facts=%s", max_chunks)

    retrieval_results_path = os.path.join(run_dir, "retrieval_results.jsonl")
    facts_path = os.path.join(run_dir, "facts.jsonl")
    results_path = os.path.join(run_dir, "results_R.jsonl")
    traces_path = os.path.join(run_dir, "calc_traces.jsonl")
    predictions_path = os.path.join(run_dir, "predictions_calc.jsonl")
    calc_used_records_path = os.path.join(run_dir, "calc_used_records.jsonl")

    extract_total = 0
    inferred_year = 0
    missing_year = 0
    missing_unit = 0
    queries_with_facts = 0
    status_counts: Counter[str] = Counter()
    task_counts: Counter[str] = Counter()
    fallback_counts: Counter[str] = Counter()
    parser_mode_counts: Counter[str] = Counter()
    parser_rule_counts: Counter[str] = Counter()
    selector_mode_counts: Counter[str] = Counter()
    selector_reason_counts: Counter[str] = Counter()
    parser_rejected_count = 0
    parser_v2_hits = 0
    selected_fact_total = 0
    selected_pair_total = 0
    soft_fallback_attempts = 0
    soft_fallback_hits = 0
    selective_pre_gate_counts: Counter[str] = Counter()
    selective_evidence_gate_counts: Counter[str] = Counter()
    selective_post_gate_counts: Counter[str] = Counter()
    selective_skip_stage_counts: Counter[str] = Counter()
    selective_skip_detail_counts: Counter[str] = Counter()
    selective_needs_calc_count = 0
    selective_calculator_used_count = 0

    with open(retrieval_results_path, "w", encoding="utf-8") as retr_f, \
        open(facts_path, "w", encoding="utf-8") as facts_f, \
        open(results_path, "w", encoding="utf-8") as results_f, \
        open(traces_path, "w", encoding="utf-8") as traces_f, \
        open(predictions_path, "w", encoding="utf-8") as preds_f, \
        open(calc_used_records_path, "w", encoding="utf-8") as used_f:
        for rec in records:
            qid = rec.get("qid")
            query = rec.get("query", "")
            if use_multistep:
                res = retrieval_results.get(qid)
                chunks = [] if not res else res.get("all_collected_chunks") or []
            else:
                retrieved = retriever.retrieve(query, top_k=top_k, alpha=alpha, mode=mode)
                chunks = [
                    {
                        "chunk_id": c.get("meta", {}).get("chunk_id"),
                        "score": c.get("score"),
                        "text": c.get("text"),
                        "meta": c.get("meta"),
                    }
                    for c in retrieved
                ]
            retr_f.write(json.dumps({"qid": qid, "all_collected_chunks": chunks}) + "\n")

            legacy_baseline_answer = placeholder_generate(query, chunks)
            selective_baseline_answer = baseline_answer_generate(chunks)
            baseline_answer = (
                selective_baseline_answer if selective_enabled else legacy_baseline_answer
            )

            pre_gate_decision: Dict[str, Any] = {"needs_calc": True, "skip_reason": None}
            needs_calc = True
            calc_skip_reason: Optional[str] = None
            calc_skip_detail: Optional[str] = None
            fallback_reason: Optional[str] = None
            calculator_used = False

            qid_facts: List[Fact] = []
            selected_facts: List[Fact] = []
            selector_audit: Dict[str, Any] = {
                "mode": fact_selector_mode,
                "reason": "no_selection",
                "selected_fact_count": 0,
                "selected_pair_count": 0,
                "selected_chunk_ids": [],
                "selected_numbers": [],
            }

            parsed = parse_task_with_lookup(
                query,
                mode=task_parser_mode,
                min_conf=task_parser_min_conf,
                enable_lookup=enable_lookup,
            )
            task_hint = parsed.task_type
            result: Optional[CalcResult] = None
            trace: Optional[CalcTrace] = None

            if selective_enabled and selective_pre_gate_enabled:
                pre_gate_decision = selective_pre_gate(
                    query,
                    pre_gate_cfg=pre_gate_cfg,
                    enable_lookup=enable_lookup,
                )
                needs_calc = bool(pre_gate_decision.get("needs_calc"))
                selective_pre_gate_counts["needs_calc" if needs_calc else "skip"] += 1
                detail = str(pre_gate_decision.get("skip_reason") or "ok")
                selective_pre_gate_counts[f"reason:{detail}"] += 1
                if needs_calc:
                    selective_needs_calc_count += 1
                else:
                    calc_skip_reason = "pre_gate"
                    calc_skip_detail = detail
                    selective_skip_stage_counts["pre_gate"] += 1
                    selective_skip_detail_counts[calc_skip_detail] += 1
                    task_hint = task_hint or pre_gate_decision.get("task_type")
                    result, trace = build_skip_result(
                        qid=str(qid),
                        task_type=task_hint,
                        reason=calc_skip_detail,
                        parsed=parsed,
                    )
                    selector_audit["reason"] = "pre_gate_skip"

            if result is None:
                for ch in (chunks[:max_chunks] if max_chunks else chunks):
                    chunk_id = ch.get("chunk_id") or ch.get("meta", {}).get("chunk_id")
                    text = ch.get("text", "")
                    if text:
                        qid_facts.extend(extract_facts_from_text(qid, chunk_id, text, query, None))
                if qid_facts:
                    queries_with_facts += 1
                for fact in qid_facts:
                    extract_total += 1
                    if fact.inferred_year:
                        inferred_year += 1
                    if fact.year is None:
                        missing_year += 1
                    if fact.unit is None:
                        missing_unit += 1
                    facts_f.write(json.dumps(fact.__dict__, ensure_ascii=False) + "\n")

                task_hint = task_hint or parsed.task_type
                selected_facts, selector_audit = select_facts(
                    query=query,
                    facts=qid_facts,
                    chunks=chunks,
                    mode=fact_selector_mode,
                    scored_cfg=fact_selector_scored,
                    task_hint=task_hint,
                )

                facts_for_compute = list(selected_facts)
                if selective_enabled and selective_evidence_gate_enabled:
                    evidence_ok, evidence_detail, evidence_facts = selective_evidence_gate(
                        query,
                        task_type=task_hint,
                        facts=selected_facts,
                        evidence_cfg=evidence_gate_cfg,
                        lookup_cfg=lookup_gate_cfg,
                    )
                    selective_evidence_gate_counts["pass" if evidence_ok else "reject"] += 1
                    selective_evidence_gate_counts[f"reason:{evidence_detail}"] += 1
                    if not evidence_ok:
                        calc_skip_reason = "evidence_gate"
                        calc_skip_detail = evidence_detail
                        selective_skip_stage_counts["evidence_gate"] += 1
                        selective_skip_detail_counts[calc_skip_detail] += 1
                        result, trace = build_skip_result(
                            qid=str(qid),
                            task_type=task_hint,
                            reason=calc_skip_detail,
                            parsed=parsed,
                        )
                    else:
                        facts_for_compute = evidence_facts

                if result is None:
                    compute_policy = None
                    if selector_top_pairs > 1:
                        compute_policy = {
                            "selector_mode": fact_selector_mode,
                            "top_groups": selector_top_groups or 1,
                            "top_pairs": selector_top_pairs,
                            "soft_fallback": False,
                        }
                    result, trace = compute_for_query(
                        query,
                        facts_for_compute,
                        output_percent,
                        task_parser_mode=task_parser_mode,
                        task_parser_min_conf=task_parser_min_conf,
                        enable_lookup=enable_lookup,
                        policy=compute_policy,
                    )

                    if (
                        selector_soft_fallback
                        and fact_selector_mode == "scored_v1"
                        and result.status != "ok"
                        and qid_facts
                    ):
                        soft_fallback_attempts += 1
                        legacy_facts, legacy_audit = select_legacy(qid_facts)
                        fallback_policy = None
                        if selector_top_pairs > 1:
                            fallback_policy = {
                                "selector_mode": "legacy_largest_group",
                                "top_groups": 1,
                                "top_pairs": selector_top_pairs,
                                "soft_fallback": False,
                            }
                        retry_result, retry_trace = compute_for_query(
                            query,
                            legacy_facts,
                            output_percent,
                            task_parser_mode=task_parser_mode,
                            task_parser_min_conf=task_parser_min_conf,
                            enable_lookup=enable_lookup,
                            policy=fallback_policy,
                        )
                        selector_audit["soft_fallback"] = {
                            "attempted": True,
                            "activated": False,
                            "fallback_status": retry_result.status,
                        }
                        if retry_result.status == "ok":
                            soft_fallback_hits += 1
                            result = retry_result
                            trace = retry_trace
                            selected_facts = legacy_facts
                            selector_audit = legacy_audit
                            selector_audit["reason"] = "soft_fallback_to_legacy_ok"
                            selector_audit["soft_fallback"] = {
                                "attempted": True,
                                "activated": True,
                                "fallback_status": retry_result.status,
                            }

            selector_mode_counts[selector_audit.get("mode", fact_selector_mode)] += 1
            selector_reason_counts[selector_audit.get("reason", "unknown")] += 1
            selected_fact_total += int(selector_audit.get("selected_fact_count", 0))
            selected_pair_total += int(selector_audit.get("selected_pair_count", 0))

            if result is None or trace is None:
                result, trace = build_skip_result(
                    qid=str(qid),
                    task_type=task_hint,
                    reason="unknown_skip",
                    parsed=parsed,
                )
                calc_skip_reason = calc_skip_reason or "compute_fail"
                calc_skip_detail = calc_skip_detail or "unknown_skip"

            result.qid = qid
            trace.qid = qid
            if selector_audit.get("soft_fallback", {}).get("attempted"):
                trace.attempted_fallback_to_legacy = True
            status_counts[result.status] += 1
            task_counts[result.task_type] += 1
            parser_mode_counts[trace.parser_mode] += 1
            if trace.parser_rule:
                parser_rule_counts[trace.parser_rule] += 1
            if trace.parser_rejected:
                parser_rejected_count += 1
            if trace.parser_mode == "v2" and trace.parser_rule:
                parser_v2_hits += 1
            results_f.write(json.dumps(result.__dict__, ensure_ascii=False) + "\n")
            traces_f.write(json.dumps(trace.__dict__, ensure_ascii=False) + "\n")

            if selective_enabled:
                if result.status == "ok":
                    if selective_post_gate_enabled:
                        post_input_cfg = dict(post_gate_cfg)
                        post_input_cfg["enabled"] = True
                        post_ok, post_detail = selective_post_gate(result, post_input_cfg)
                    else:
                        post_ok, post_detail = True, "ok"
                    selective_post_gate_counts["pass" if post_ok else "reject"] += 1
                    selective_post_gate_counts[f"reason:{post_detail}"] += 1
                    if post_ok:
                        calculator_used = True
                        selective_calculator_used_count += 1
                        used_chunks = [
                            i.get("chunk_id") for i in result.inputs if i.get("chunk_id")
                        ]
                        calc_head = (
                            f"Result: {result.result_value} {result.result_unit or ''}".strip()
                        )
                        pred_answer = f"{calc_head}. {baseline_answer}".strip()
                        fallback_reason = None
                        calc_skip_reason = None
                        calc_skip_detail = None
                    else:
                        calc_skip_reason = "post_gate"
                        calc_skip_detail = post_detail
                        selective_skip_stage_counts["post_gate"] += 1
                        selective_skip_detail_counts[calc_skip_detail] += 1
                        used_chunks = [c.get("chunk_id") for c in chunks if c.get("chunk_id")]
                        pred_answer = baseline_answer
                        fallback_reason = calc_skip_detail
                        fallback_counts[fallback_reason] += 1
                else:
                    if calc_skip_reason is None:
                        calc_skip_reason = "compute_fail"
                        calc_skip_detail = f"status_{result.status}"
                    if calc_skip_detail is None:
                        calc_skip_detail = "status_unknown"
                    used_chunks = [c.get("chunk_id") for c in chunks if c.get("chunk_id")]
                    pred_answer = baseline_answer
                    fallback_reason = calc_skip_detail
                    fallback_counts[fallback_reason] += 1
            else:
                gate_cfg = get_path(resolved, "calculator.gate", {}) or {}
                allow_tasks = gate_cfg.get("allow_task_types", ["yoy", "diff"])
                min_conf = float(gate_cfg.get("min_conf", 0.0))
                require_unit = bool(gate_cfg.get("require_unit_consistency", True))
                require_year = bool(gate_cfg.get("require_year_match", True))
                allow_inferred = bool(gate_cfg.get("allow_inferred", False))
                gate_reason = None
                if gate_cfg.get("enabled", True):
                    if result.task_type not in allow_tasks:
                        gate_reason = "gate_task"
                    elif result.status != "ok":
                        gate_reason = f"status_{result.status}"
                    elif result.confidence < min_conf:
                        gate_reason = "gate_conf"
                    else:
                        units = [i.get("unit") for i in result.inputs]
                        if require_unit and units and len({u for u in units if u}) > 1:
                            gate_reason = "gate_unit"
                        if require_year and result.task_type == "yoy":
                            years = [i.get("year") for i in result.inputs]
                            inferred = [bool(i.get("inferred_year")) for i in result.inputs]
                            if any(y is None for y in years):
                                gate_reason = "gate_year"
                            if any(inferred) and not allow_inferred:
                                gate_reason = "gate_inferred"

                if result.status == "ok" and gate_reason is None:
                    calculator_used = True
                    used_chunks = [i.get("chunk_id") for i in result.inputs if i.get("chunk_id")]
                    unit = result.result_unit or ""
                    pred_answer = f"Result: {result.result_value} {unit}. {result.explanation}"
                    fallback_reason = None
                else:
                    used_chunks = [c.get("chunk_id") for c in chunks if c.get("chunk_id")]
                    pred_answer = placeholder_generate(query, chunks)
                    fallback_reason = gate_reason or result.status
                    fallback_counts[fallback_reason] += 1

            preds_f.write(
                json.dumps(
                    {
                        "qid": qid,
                        "pred_answer": pred_answer,
                        "used_chunks": used_chunks,
                        "R": result.__dict__,
                        "fallback_reason": fallback_reason,
                        "calculator_used": calculator_used,
                        "calc_skip_reason": calc_skip_reason,
                        "calc_skip_detail": calc_skip_detail,
                        "needs_calc": bool(pre_gate_decision.get("needs_calc"))
                        if selective_enabled
                        else None,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

            selected_chunk_ids = [i.get("chunk_id") for i in result.inputs if i.get("chunk_id")]
            if not selected_chunk_ids:
                selected_chunk_ids = selector_audit.get("selected_chunk_ids", [])
            selected_numbers = [i.get("value") for i in result.inputs if i.get("value") is not None]
            if not selected_numbers:
                selected_numbers = selector_audit.get("selected_numbers", [])

            used_f.write(
                json.dumps(
                    {
                        "qid": qid,
                        "task_type": result.task_type,
                        "task_parser": {
                            "mode": trace.parser_mode,
                            "confidence": trace.parser_confidence,
                            "rule": trace.parser_rule,
                            "rejected": trace.parser_rejected,
                            "scores": trace.parser_scores,
                            "rules": trace.parser_rules,
                        },
                        "fact_selector_mode": selector_audit.get("mode", fact_selector_mode),
                        "selected_chunk_ids": selected_chunk_ids,
                        "selected_numbers": selected_numbers,
                        "score_breakdown": {
                            "reason": selector_audit.get("reason"),
                            "top_groups": selector_audit.get("top_groups"),
                            "selected_group_keys": selector_audit.get("selected_group_keys", []),
                            "group_scores_top": selector_audit.get("group_scores_top", []),
                            "top_fact_scores": selector_audit.get("top_fact_scores", []),
                            "selected_pairs": selector_audit.get("selected_pairs", []),
                            "soft_fallback": selector_audit.get("soft_fallback", {}),
                        },
                        "compute_trace": {
                            "selector_mode": trace.selector_mode,
                            "tried_group_keys": trace.tried_group_keys,
                            "tried_pair_count": trace.tried_pair_count,
                            "attempted_fallback_to_legacy": trace.attempted_fallback_to_legacy,
                        },
                        "final_result": {
                            "status": result.status,
                            "confidence": result.confidence,
                            "result_value": result.result_value,
                            "result_unit": result.result_unit,
                            "explanation": result.explanation,
                        },
                        "fallback_reason": fallback_reason,
                        "calculator_used": calculator_used,
                        "calc_skip_reason": calc_skip_reason,
                        "calc_skip_detail": calc_skip_detail,
                        "needs_calc": bool(pre_gate_decision.get("needs_calc"))
                        if selective_enabled
                        else None,
                        "pre_gate_audit": pre_gate_decision if selective_enabled else {},
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    total = len(records)
    extract_stats = {
        "total_queries": total,
        "queries_with_facts": queries_with_facts,
        "no_fact_ratio": 1.0 - (queries_with_facts / total) if total else 0.0,
        "total_facts": extract_total,
        "facts_per_query": extract_total / total if total else 0.0,
        "max_chunks_for_facts": max_chunks,
        "inferred_year_ratio": inferred_year / extract_total if extract_total else 0.0,
        "missing_year_ratio": missing_year / extract_total if extract_total else 0.0,
        "missing_unit_ratio": missing_unit / extract_total if extract_total else 0.0,
    }
    fallback_total = sum(fallback_counts.values())
    calc_stats = {
        "total_queries": total,
        "ok_ratio": status_counts.get("ok", 0) / total if total else 0.0,
        "fallback_ratio": fallback_total / total if total else 0.0,
        "status_counts": dict(status_counts),
        "task_counts": dict(task_counts),
        "fallback_counts": dict(fallback_counts),
        "task_parser_stats": {
            "mode_counts": dict(parser_mode_counts),
            "rule_counts": dict(parser_rule_counts),
            "rejected_count": parser_rejected_count,
            "v2_rule_hit_count": parser_v2_hits,
            "v2_hit_rate": parser_v2_hits / total if total else 0.0,
            "configured_mode": task_parser_mode,
            "configured_min_conf": task_parser_min_conf,
        },
        "fact_selector_stats": {
            "mode_counts": dict(selector_mode_counts),
            "reason_counts": dict(selector_reason_counts),
            "selected_fact_count_mean": selected_fact_total / total if total else 0.0,
            "selected_pair_count_mean": selected_pair_total / total if total else 0.0,
            "configured_mode": fact_selector_mode,
            "configured_scored_v1": fact_selector_scored,
            "configured_selector_mode": get_path(resolved, "calculator.selector.mode", None),
            "configured_selector_top_groups": selector_top_groups,
            "configured_execution_top_pairs": selector_top_pairs,
            "soft_fallback_enabled": selector_soft_fallback,
            "soft_fallback_attempts": soft_fallback_attempts,
            "soft_fallback_hits": soft_fallback_hits,
        },
        "selective_stats": {
            "enabled": selective_enabled,
            "pre_gate_enabled": selective_pre_gate_enabled,
            "evidence_gate_enabled": selective_evidence_gate_enabled,
            "post_gate_enabled": selective_post_gate_enabled,
            "pre_gate_counts": dict(selective_pre_gate_counts),
            "evidence_gate_counts": dict(selective_evidence_gate_counts),
            "post_gate_counts": dict(selective_post_gate_counts),
            "skip_stage_counts": dict(selective_skip_stage_counts),
            "skip_detail_counts": dict(selective_skip_detail_counts),
            "needs_calc_ratio": selective_needs_calc_count / total if total else 0.0,
            "calculator_used_ratio": selective_calculator_used_count / total if total else 0.0,
            "needs_calc_count": selective_needs_calc_count,
            "calculator_used_count": selective_calculator_used_count,
            "lookup_enabled": enable_lookup,
        },
        "results_path": results_path,
        "traces_path": traces_path,
        "calc_used_records_path": calc_used_records_path,
    }
    with open(os.path.join(run_dir, "extract_stats.json"), "w", encoding="utf-8") as f:
        json.dump(extract_stats, f, indent=2)
    with open(os.path.join(run_dir, "calc_stats.json"), "w", encoding="utf-8") as f:
        json.dump(calc_stats, f, indent=2)
    with open(os.path.join(run_dir, "git_commit.txt"), "w", encoding="utf-8") as f:
        f.write(f"{git_hash}\n")
    save_config(resolved, os.path.join(run_dir, "config.yaml"))
    logger.info("extract_stats=%s", extract_stats)
    logger.info("calc_stats=%s", calc_stats)
    logger.info("predictions_path=%s", predictions_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
