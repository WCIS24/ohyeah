from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from typing import Any, Dict, List, Tuple

import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from calculator.compute import parse_task_with_lookup  # noqa: E402
from calculator.value_task import numeric_intent  # noqa: E402
from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402
from training.pairs import load_jsonl  # noqa: E402

ARITHMETIC_TASKS = {"yoy", "diff", "share", "multiple"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build calc-needed/value-needed subsets")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    return parser.parse_args()


def file_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_qid_file(path: str, qids: List[str]) -> Dict[str, Any]:
    with open(path, "w", encoding="utf-8") as f:
        for qid in qids:
            f.write(f"{qid}\n")
    return {
        "path": path,
        "count": len(qids),
        "sha256": file_sha256(path),
    }


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def classify_query(
    query: str,
    *,
    calc_mode: str,
    calc_min_conf: float,
    value_mode: str,
    value_lookup_min_conf: float,
    include_lookup: bool,
    use_numeric_intent_fallback: bool,
) -> Tuple[bool, str, bool, str, Dict[str, Any]]:
    calc_parse = parse_task_with_lookup(
        query,
        mode=calc_mode,
        min_conf=calc_min_conf,
        enable_lookup=False,
    )
    calc_conf = float(calc_parse.confidence)
    is_calc = calc_parse.task_type in ARITHMETIC_TASKS and calc_conf >= calc_min_conf
    calc_reason = str(calc_parse.rule or calc_parse.task_type or "no_calc_match")

    value_parse = parse_task_with_lookup(
        query,
        mode=value_mode,
        min_conf=value_lookup_min_conf,
        enable_lookup=include_lookup,
    )
    value_conf = float(value_parse.confidence)
    lookup_hit = (
        value_parse.task_type == "lookup"
        and value_conf >= value_lookup_min_conf
        and include_lookup
    )
    numeric_hit = bool(numeric_intent(query))

    is_value = False
    value_reason = "no_value_match"
    if not is_calc:
        if lookup_hit:
            is_value = True
            value_reason = str(value_parse.rule or "lookup_parser")
        elif use_numeric_intent_fallback and numeric_hit:
            is_value = True
            value_reason = "numeric_intent_fallback"

    audit = {
        "calc_parse": {
            "task_type": calc_parse.task_type,
            "confidence": calc_conf,
            "rule": calc_parse.rule,
            "mode": calc_parse.mode,
        },
        "value_parse": {
            "task_type": value_parse.task_type,
            "confidence": value_conf,
            "rule": value_parse.rule,
            "mode": value_parse.mode,
        },
        "numeric_intent": numeric_hit,
    }
    return is_calc, calc_reason, is_value, value_reason, audit


def main() -> int:
    args = parse_args()
    config = load_config(args.config)

    run_id = config.get("run_id") or generate_run_id()
    config["run_id"] = run_id
    output_dir = config.get("output_dir", "outputs")
    run_dir = os.path.join(output_dir, run_id)
    ensure_dir(run_dir)

    log_path = os.path.join(run_dir, "logs.txt")
    logger = setup_logging(log_path)
    logger.info("command_line=%s", " ".join(sys.argv))
    logger.info("config_path=%s", args.config)

    git_hash = get_git_hash()
    config["git_hash"] = git_hash
    logger.info("git_hash=%s", git_hash)

    seed = int(config.get("seed", 42))
    random.seed(seed)
    np.random.seed(seed)
    logger.info("seed=%d", seed)

    processed_path = config.get("processed_dev_path", "data/processed/dev.jsonl")
    subsets_dir = config.get("subsets_dir", "data/subsets")
    ensure_dir(subsets_dir)

    calc_cfg = config.get("calc", {}) or {}
    value_cfg = config.get("value", {}) or {}
    calc_mode = str(calc_cfg.get("parser_mode", "v2")).lower().strip()
    value_mode = str(value_cfg.get("parser_mode", calc_mode)).lower().strip()
    calc_min_conf = _to_float(calc_cfg.get("min_conf", 0.45), 0.45)
    value_lookup_min_conf = _to_float(value_cfg.get("lookup_min_conf", 0.45), 0.45)
    include_lookup = bool(value_cfg.get("include_lookup", True))
    use_numeric_intent_fallback = bool(value_cfg.get("use_numeric_intent_fallback", True))
    calc_subset_name = str(calc_cfg.get("subset_filename", "dev_calc_needed_qids.txt"))
    value_subset_name = str(value_cfg.get("subset_filename", "dev_value_needed_qids.txt"))

    logger.info(
        "processed_dev_path=%s subsets_dir=%s calc_mode=%s calc_min_conf=%.3f "
        "value_mode=%s value_lookup_min_conf=%.3f include_lookup=%s "
        "numeric_intent_fallback=%s",
        processed_path,
        subsets_dir,
        calc_mode,
        calc_min_conf,
        value_mode,
        value_lookup_min_conf,
        include_lookup,
        use_numeric_intent_fallback,
    )

    records = load_jsonl(processed_path)
    calc_qids: List[str] = []
    value_qids: List[str] = []
    calc_reason_counts: Dict[str, int] = {}
    calc_task_counts: Dict[str, int] = {}
    value_reason_counts: Dict[str, int] = {}
    value_task_counts: Dict[str, int] = {}
    numeric_intent_hits = 0
    query_audit_rows: List[Dict[str, Any]] = []

    for rec in records:
        qid = str(rec.get("qid"))
        query = str(rec.get("query", ""))
        is_calc, calc_reason, is_value, value_reason, audit = classify_query(
            query,
            calc_mode=calc_mode,
            calc_min_conf=calc_min_conf,
            value_mode=value_mode,
            value_lookup_min_conf=value_lookup_min_conf,
            include_lookup=include_lookup,
            use_numeric_intent_fallback=use_numeric_intent_fallback,
        )

        if audit["numeric_intent"]:
            numeric_intent_hits += 1

        calc_task = audit["calc_parse"]["task_type"] or "none"
        value_task = audit["value_parse"]["task_type"] or "none"
        calc_task_counts[calc_task] = calc_task_counts.get(calc_task, 0) + 1
        value_task_counts[value_task] = value_task_counts.get(value_task, 0) + 1

        if is_calc:
            calc_qids.append(qid)
            calc_reason_counts[calc_reason] = calc_reason_counts.get(calc_reason, 0) + 1
        if is_value:
            value_qids.append(qid)
            value_reason_counts[value_reason] = value_reason_counts.get(value_reason, 0) + 1

        if len(query_audit_rows) < 20:
            query_audit_rows.append(
                {
                    "qid": qid,
                    "query": query,
                    "is_calc": is_calc,
                    "calc_reason": calc_reason,
                    "is_value": is_value,
                    "value_reason": value_reason,
                    "audit": audit,
                }
            )

    calc_path = os.path.join(subsets_dir, calc_subset_name)
    value_path = os.path.join(subsets_dir, value_subset_name)
    calc_file = write_qid_file(calc_path, calc_qids)
    value_file = write_qid_file(value_path, value_qids)

    metrics = {
        "git_hash": git_hash,
        "seed": seed,
        "processed_dev_path": processed_path,
        "records_total": len(records),
        "query_only": True,
        "reads_answer_field": False,
        "calc_subset": {
            **calc_file,
            "ratio": len(calc_qids) / len(records) if records else 0.0,
            "parser_mode": calc_mode,
            "min_conf": calc_min_conf,
            "reason_counts": calc_reason_counts,
            "task_counts": calc_task_counts,
        },
        "value_subset": {
            **value_file,
            "ratio": len(value_qids) / len(records) if records else 0.0,
            "parser_mode": value_mode,
            "lookup_min_conf": value_lookup_min_conf,
            "include_lookup": include_lookup,
            "use_numeric_intent_fallback": use_numeric_intent_fallback,
            "reason_counts": value_reason_counts,
            "task_counts": value_task_counts,
            "numeric_intent_hits": numeric_intent_hits,
        },
        "overlap_count": len(set(calc_qids) & set(value_qids)),
    }

    metrics_path = os.path.join(run_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    audit_path = os.path.join(run_dir, "query_audit_sample.json")
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(query_audit_rows, f, indent=2, ensure_ascii=False)

    with open(os.path.join(run_dir, "git_commit.txt"), "w", encoding="utf-8") as f:
        f.write(f"{git_hash}\n")

    save_config(config, os.path.join(run_dir, "config.yaml"))

    logger.info(
        "calc_subset path=%s count=%d sha256=%s",
        calc_file["path"],
        calc_file["count"],
        calc_file["sha256"],
    )
    logger.info(
        "value_subset path=%s count=%d sha256=%s",
        value_file["path"],
        value_file["count"],
        value_file["sha256"],
    )
    logger.info("metrics=%s", metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
