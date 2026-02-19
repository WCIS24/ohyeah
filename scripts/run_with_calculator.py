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

from calculator.compute import compute_for_query, group_facts, parse_task, select_group  # noqa: E402
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

VALID_FACT_SELECTOR_MODES = {"legacy_largest_group", "scored_v1"}
VALID_TASK_PARSER_MODES = {"v1", "v2"}


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

    task_parser_mode = str(get_path(resolved, "calculator.task_parser.mode", "v1")).lower().strip()
    if task_parser_mode not in VALID_TASK_PARSER_MODES:
        logger.warning("invalid calculator.task_parser.mode=%s fallback=v1", task_parser_mode)
        task_parser_mode = "v1"
    task_parser_min_conf = float(get_path(resolved, "calculator.task_parser.v2.min_conf", 0.45))

    fact_selector_mode = str(
        get_path(resolved, "calculator.fact_selector.mode", "legacy_largest_group")
    ).lower().strip()
    if fact_selector_mode not in VALID_FACT_SELECTOR_MODES:
        logger.warning("invalid calculator.fact_selector.mode=%s fallback=legacy", fact_selector_mode)
        fact_selector_mode = "legacy_largest_group"
    fact_selector_scored = get_path(resolved, "calculator.fact_selector.scored_v1", {}) or {}

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
        "retriever_mode=%s top_k=%d alpha=%.3f output_percent=%s", mode, top_k, alpha, output_percent
    )
    logger.info(
        "task_parser mode=%s min_conf=%.3f fact_selector mode=%s",
        task_parser_mode,
        task_parser_min_conf,
        fact_selector_mode,
    )
    logger.info("fact_selector_scored_v1=%s", fact_selector_scored)
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

            qid_facts: List[Fact] = []
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

            parsed = parse_task(query, mode=task_parser_mode, min_conf=task_parser_min_conf)
            selected_facts, selector_audit = select_facts(
                query=query,
                facts=qid_facts,
                chunks=chunks,
                mode=fact_selector_mode,
                scored_cfg=fact_selector_scored,
                task_hint=parsed.task_type,
            )
            selector_mode_counts[selector_audit.get("mode", fact_selector_mode)] += 1
            selector_reason_counts[selector_audit.get("reason", "unknown")] += 1
            selected_fact_total += int(selector_audit.get("selected_fact_count", 0))
            selected_pair_total += int(selector_audit.get("selected_pair_count", 0))

            result, trace = compute_for_query(
                query,
                selected_facts,
                output_percent,
                task_parser_mode=task_parser_mode,
                task_parser_min_conf=task_parser_min_conf,
            )
            result.qid = qid
            trace.qid = qid
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
                            "top_fact_scores": selector_audit.get("top_fact_scores", []),
                            "selected_pairs": selector_audit.get("selected_pairs", []),
                        },
                        "final_result": {
                            "status": result.status,
                            "confidence": result.confidence,
                            "result_value": result.result_value,
                            "result_unit": result.result_unit,
                            "explanation": result.explanation,
                        },
                        "fallback_reason": fallback_reason,
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
