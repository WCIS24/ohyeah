from __future__ import annotations

import argparse
import json
import os
import re
import sys
from statistics import mean, median
from typing import Any, Dict, List, Optional

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402
from training.pairs import load_jsonl  # noqa: E402
from config.schema import (  # noqa: E402
    get_path,
    resolve_config,
    validate_config,
    validate_paths,
    write_resolved_config,
)

NUMBER_RE = re.compile(r"[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate numeric answers")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--predictions", default=None, help="Override predictions path")
    parser.add_argument("--subset-qids", default=None, help="Optional subset qid list")
    parser.add_argument("--baseline-metrics", default=None, help="Optional baseline metrics path")
    return parser.parse_args()


def apply_overrides(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    if args.predictions is not None:
        config["predictions_path"] = args.predictions
    if args.subset_qids is not None:
        config["subset_qids_path"] = args.subset_qids
    if args.baseline_metrics is not None:
        config["baseline_metrics_path"] = args.baseline_metrics
    return config


def load_subset(path: Optional[str]) -> Optional[set[str]]:
    if not path or str(path).lower() in {"none", "null"}:
        return None
    qids = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            qid = line.strip()
            if qid:
                qids.add(qid)
    return qids


def extract_numbers(text: str) -> List[Dict[str, object]]:
    nums = []
    for match in NUMBER_RE.finditer(text or ""):
        num_str = match.group(0).replace(",", "")
        try:
            val = float(num_str)
        except ValueError:
            continue
        window = (text or "")[match.end() : match.end() + 5]
        is_percent = "%" in window or "percent" in window.lower()
        nums.append({"value": val, "is_percent": is_percent})
    return nums


def normalize_percent_mode(
    gold: Dict[str, object],
    pred: Dict[str, object],
    mode: str,
) -> float:
    gold_val = float(gold["value"])
    pred_val = float(pred["value"])
    gold_pct = bool(gold.get("is_percent"))
    pred_pct = bool(pred.get("is_percent"))
    if mode != "auto":
        return pred_val
    if gold_pct == pred_pct:
        return pred_val
    candidates = [pred_val, pred_val * 100.0, pred_val / 100.0]
    best = min(candidates, key=lambda v: abs(v - gold_val))
    return best


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
    logger.info("seed=%d", seed)
    logger.info(
        "dense_model=%s alpha=%.3f chunk_size=%d overlap=%d",
        get_path(resolved, "retriever.dense.model_name_or_path"),
        float(get_path(resolved, "retriever.hybrid.alpha", 0.5)),
        int(get_path(resolved, "chunking.chunk_size", 0)),
        int(get_path(resolved, "chunking.overlap", 0)),
    )

    predictions_path = raw_config.get("predictions_path")
    if not predictions_path or not os.path.exists(predictions_path):
        logger.error("missing predictions_path: %s", predictions_path)
        return 2
    logger.info(
        "predictions_path=%s subset_qids_path=%s",
        predictions_path,
        raw_config.get("subset_qids_path"),
    )

    processed_dir = get_path(resolved, "data.processed_dir", "data/processed")
    dev_file = get_path(resolved, "data.splits.dev", "dev.jsonl")
    dev_path = os.path.join(processed_dir, dev_file)
    records = load_jsonl(dev_path)
    preds = {p.get("qid"): p for p in load_jsonl(predictions_path)}

    subset_qids = load_subset(raw_config.get("subset_qids_path"))
    if subset_qids:
        records = [r for r in records if r.get("qid") in subset_qids]

    precision = int(get_path(resolved, "eval.numeric.tolerance", 4))
    normalize_mode = get_path(resolved, "eval.numeric.normalize_percent_mode", "auto")

    per_query_path = os.path.join(run_dir, "numeric_per_query.jsonl")
    em_list: List[int] = []
    abs_errors: List[float] = []
    rel_errors: List[float] = []

    missing_pred = 0
    missing_gold = 0
    multi_pred = 0
    multi_gold = 0

    with open(per_query_path, "w", encoding="utf-8") as f:
        for rec in records:
            qid = rec.get("qid")
            gold = rec.get("answer", "")
            pred = preds.get(qid, {}).get("pred_answer", "")

            gold_nums = extract_numbers(gold)
            pred_nums = extract_numbers(pred)

            if len(gold_nums) > 1:
                multi_gold += 1
            if len(pred_nums) > 1:
                multi_pred += 1

            gold_val = gold_nums[0] if gold_nums else None
            pred_val = pred_nums[0] if pred_nums else None

            extracted_ok = pred_val is not None
            if pred_val is None:
                missing_pred += 1
            if gold_val is None:
                missing_gold += 1

            abs_err = None
            rel_err = None
            em = 0
            if gold_val is not None and pred_val is not None:
                pred_num = normalize_percent_mode(gold_val, pred_val, normalize_mode)
                abs_err = abs(pred_num - float(gold_val["value"]))
                denom = max(abs(float(gold_val["value"])), 1e-9)
                rel_err = abs_err / denom
                em = int(round(pred_num, precision) == round(float(gold_val["value"]), precision))
                abs_errors.append(abs_err)
                rel_errors.append(rel_err)
                em_list.append(em)

            f.write(
                json.dumps(
                    {
                        "qid": qid,
                        "gold_num": gold_val["value"] if gold_val is not None else None,
                        "pred_num": pred_val["value"] if pred_val is not None else None,
                        "abs_err": abs_err,
                        "rel_err": rel_err,
                        "numeric_em": em,
                        "extracted_ok": extracted_ok,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    coverage = 1.0 - (missing_pred / len(records)) if records else 0.0
    metrics = {
        "total_queries": len(records),
        "coverage": coverage,
        "numeric_em": mean(em_list) if em_list else 0.0,
        "abs_error_mean": mean(abs_errors) if abs_errors else None,
        "abs_error_median": median(abs_errors) if abs_errors else None,
        "rel_error_mean": mean(rel_errors) if rel_errors else None,
        "rel_error_median": median(rel_errors) if rel_errors else None,
        "missing_pred": missing_pred,
        "missing_gold": missing_gold,
        "multi_pred": multi_pred,
        "multi_gold": multi_gold,
        "predictions_path": predictions_path,
    }

    metrics_path = os.path.join(run_dir, "numeric_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    baseline_path = raw_config.get("baseline_metrics_path")
    if baseline_path and os.path.exists(baseline_path):
        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline = json.load(f)
        delta = {}
        for key in [
            "numeric_em",
            "rel_error_mean",
            "rel_error_median",
            "abs_error_mean",
            "abs_error_median",
            "coverage",
        ]:
            if metrics.get(key) is not None and baseline.get(key) is not None:
                delta[key] = metrics[key] - baseline[key]
        delta_path = os.path.join(run_dir, "delta_vs_baseline.json")
        with open(delta_path, "w", encoding="utf-8") as f:
            json.dump({"delta": delta, "baseline": baseline, "current": metrics}, f, indent=2)
        logger.info("delta_vs_baseline=%s", delta)

    with open(os.path.join(run_dir, "git_commit.txt"), "w", encoding="utf-8") as f:
        f.write(f"{git_hash}\n")

    config_out = os.path.join(run_dir, "config.yaml")
    save_config(resolved, config_out)

    logger.info("metrics=%s", metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
