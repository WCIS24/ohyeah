from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import Counter
from typing import Any, Dict, List, Optional

import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from calculator.compute import compute_for_query  # noqa: E402
from calculator.extract import extract_facts_from_text  # noqa: E402
from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402
from retrieval.query_expansion import build_query_expander_from_config  # noqa: E402
from retrieval.retriever import HybridRetriever  # noqa: E402
from training.pairs import load_jsonl  # noqa: E402
from config.schema import (  # noqa: E402
    get_path,
    resolve_config,
    validate_config,
    validate_paths,
    write_resolved_config,
)


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
    dev_path = os.path.join(processed_dir, dev_file)
    records = load_jsonl(dev_path)

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

    retrieval_results_path = os.path.join(run_dir, "retrieval_results.jsonl")
    facts_path = os.path.join(run_dir, "facts.jsonl")
    results_path = os.path.join(run_dir, "results_R.jsonl")
    traces_path = os.path.join(run_dir, "calc_traces.jsonl")
    predictions_path = os.path.join(run_dir, "predictions_calc.jsonl")

    output_percent = bool(get_path(resolved, "calculator.parsing.output_percent", True))
    top_k = int(get_path(resolved, "retriever.top_k", 5))
    alpha = float(get_path(resolved, "retriever.hybrid.alpha", 0.5))
    mode = get_path(resolved, "retriever.mode", "dense")
    chunk_size = int(get_path(resolved, "chunking.chunk_size", 0))
    overlap = int(get_path(resolved, "chunking.overlap", 0))
    logger.info("use_multistep=%s multistep_results_path=%s", use_multistep, multistep_path)
    logger.info(
        "retriever_mode=%s top_k=%d alpha=%.3f output_percent=%s",
        mode,
        top_k,
        alpha,
        output_percent,
    )
    logger.info(
        "dense_model=%s chunk_size=%d overlap=%d",
        get_path(resolved, "retriever.dense.model_name_or_path"),
        chunk_size,
        overlap,
    )
    logger.info(
        "qexpand_enabled=%s max_queries=%s boost=%s",
        bool(get_path(resolved, "qexpand.enabled", False)),
        get_path(resolved, "qexpand.max_queries", None),
        get_path(resolved, "qexpand.boost", None),
    )

    extract_total = 0
    inferred_year = 0
    missing_year = 0
    missing_unit = 0
    queries_with_facts = 0

    status_counts: Counter[str] = Counter()
    task_counts: Counter[str] = Counter()
    fallback_counts: Counter[str] = Counter()

    with open(retrieval_results_path, "w", encoding="utf-8") as retr_f, \
        open(facts_path, "w", encoding="utf-8") as facts_f, \
        open(results_path, "w", encoding="utf-8") as results_f, \
        open(traces_path, "w", encoding="utf-8") as traces_f, \
        open(predictions_path, "w", encoding="utf-8") as preds_f:
        for rec in records:
            qid = rec.get("qid")
            query = rec.get("query", "")

            if use_multistep:
                res = retrieval_results.get(qid)
                if not res:
                    chunks = []
                else:
                    chunks = res.get("all_collected_chunks") or res.get("final_top_chunks") or []
            else:
                chunks = retriever.retrieve(query, top_k=top_k, alpha=alpha, mode=mode)
                chunks = [
                    {
                        "chunk_id": c.get("meta", {}).get("chunk_id"),
                        "score": c.get("score"),
                        "text": c.get("text"),
                        "meta": c.get("meta"),
                    }
                    for c in chunks
                ]

            retr_f.write(json.dumps({"qid": qid, "all_collected_chunks": chunks}) + "\n")

            qid_facts: List[Fact] = []
            for ch in chunks:
                chunk_id = ch.get("chunk_id") or ch.get("meta", {}).get("chunk_id")
                text = ch.get("text", "")
                if not text:
                    continue
                facts = extract_facts_from_text(qid, chunk_id, text, query, None)
                qid_facts.extend(facts)

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

            result, trace = compute_for_query(query, qid_facts, output_percent)
            result.qid = qid
            trace.qid = qid
            status_counts[result.status] += 1
            task_counts[result.task_type] += 1

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
                used_chunks = [u for u in used_chunks if u]
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

    extract_stats = {
        "total_queries": len(records),
        "queries_with_facts": queries_with_facts,
        "no_fact_ratio": 1.0 - (queries_with_facts / len(records)) if records else 0.0,
        "total_facts": extract_total,
        "facts_per_query": extract_total / len(records) if records else 0.0,
        "inferred_year_ratio": inferred_year / extract_total if extract_total else 0.0,
        "missing_year_ratio": missing_year / extract_total if extract_total else 0.0,
        "missing_unit_ratio": missing_unit / extract_total if extract_total else 0.0,
    }

    calc_stats = {
        "total_queries": len(records),
        "ok_ratio": status_counts.get("ok", 0) / len(records) if records else 0.0,
        "status_counts": dict(status_counts),
        "task_counts": dict(task_counts),
        "fallback_counts": dict(fallback_counts),
        "results_path": results_path,
        "traces_path": traces_path,
    }

    extract_stats_path = os.path.join(run_dir, "extract_stats.json")
    with open(extract_stats_path, "w", encoding="utf-8") as f:
        json.dump(extract_stats, f, indent=2)

    calc_stats_path = os.path.join(run_dir, "calc_stats.json")
    with open(calc_stats_path, "w", encoding="utf-8") as f:
        json.dump(calc_stats, f, indent=2)

    with open(os.path.join(run_dir, "git_commit.txt"), "w", encoding="utf-8") as f:
        f.write(f"{git_hash}\n")

    config_out = os.path.join(run_dir, "config.yaml")
    save_config(resolved, config_out)

    logger.info("extract_stats=%s", extract_stats)
    logger.info("calc_stats=%s", calc_stats)
    logger.info("predictions_path=%s", predictions_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
