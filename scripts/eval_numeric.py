from __future__ import annotations

import argparse
from collections import Counter
import json
import os
import re
import sys
from statistics import mean, median
from typing import Any, Dict, List, Optional, Tuple

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
    set_path,
    validate_config,
    validate_paths,
    write_resolved_config,
)

NUMBER_RE = re.compile(r"[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?")
RESULT_TAG_VALUE_RE = re.compile(
    r"(?i)\b(?:result|answer)\s*[:=]\s*([-+]?\d+(?:,\d{3})*(?:\.\d+)?)"
)
VALID_EXTRACT_STRATEGIES = {"first", "last", "result_tag"}


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


def _coerce_int(value: Any, key_name: str, fallback: int, logger) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        logger.warning("invalid %s=%r; fallback to %d", key_name, value, fallback)
        return fallback


def resolve_numeric_tolerance(raw_config: Dict[str, Any], resolved: Dict[str, Any], logger) -> int:
    fallback = int(get_path(resolved, "eval.numeric.tolerance", 4))
    nested_tol = get_path(raw_config, "eval.numeric.tolerance", None)
    legacy_tol = raw_config.get("tolerance")
    legacy_precision = raw_config.get("precision")

    if nested_tol is not None:
        tolerance = _coerce_int(nested_tol, "eval.numeric.tolerance", fallback, logger)
        if legacy_tol is not None or legacy_precision is not None:
            logger.warning(
                "both new and legacy numeric keys provided; "
                "use eval.numeric.tolerance=%d and ignore legacy keys",
                tolerance,
            )
        source = "eval.numeric.tolerance"
    elif legacy_tol is not None:
        tolerance = _coerce_int(legacy_tol, "tolerance", fallback, logger)
        if legacy_precision is not None:
            logger.warning(
                "both legacy keys provided; use tolerance=%d and ignore precision=%r",
                tolerance,
                legacy_precision,
            )
        logger.warning(
            "deprecated key 'tolerance' is used; please migrate to eval.numeric.tolerance"
        )
        source = "legacy:tolerance"
    elif legacy_precision is not None:
        tolerance = _coerce_int(legacy_precision, "precision", fallback, logger)
        logger.warning(
            "deprecated key 'precision' is used; please migrate to eval.numeric.tolerance"
        )
        source = "legacy:precision"
    else:
        tolerance = fallback
        source = "default"

    set_path(resolved, "eval.numeric.tolerance", tolerance)
    logger.info("numeric_tolerance=%d source=%s", tolerance, source)
    return tolerance


def resolve_extract_strategy(raw_config: Dict[str, Any], resolved: Dict[str, Any], logger) -> str:
    raw_strategy = get_path(raw_config, "eval.numeric.extract_strategy", None)
    default_strategy = str(get_path(resolved, "eval.numeric.extract_strategy", "first"))
    strategy = raw_strategy if raw_strategy is not None else default_strategy

    if not isinstance(strategy, str):
        logger.warning("invalid eval.numeric.extract_strategy=%r; fallback to 'first'", strategy)
        strategy = "first"
    strategy = strategy.strip().lower()
    if strategy not in VALID_EXTRACT_STRATEGIES:
        logger.warning(
            "unsupported eval.numeric.extract_strategy=%r; allowed=%s; fallback to 'first'",
            strategy,
            sorted(VALID_EXTRACT_STRATEGIES),
        )
        strategy = "first"
    set_path(resolved, "eval.numeric.extract_strategy", strategy)
    logger.info("numeric_extract_strategy=%s", strategy)
    return strategy


def extract_result_tag_number(text: str) -> Optional[Dict[str, object]]:
    if not text:
        return None
    match = RESULT_TAG_VALUE_RE.search(text)
    if match is None:
        return None
    num_str = match.group(1).replace(",", "")
    try:
        value = float(num_str)
    except ValueError:
        return None
    window = text[match.end(1) : match.end(1) + 8]
    is_percent = "%" in window or "percent" in window.lower()
    return {"value": value, "is_percent": is_percent}


def pick_number(
    text: str,
    numbers: List[Dict[str, object]],
    strategy: str,
) -> Tuple[Optional[Dict[str, object]], str]:
    if not numbers:
        return None, "missing"
    if strategy == "first":
        return numbers[0], "first"
    if strategy == "last":
        return numbers[-1], "last"
    tagged = extract_result_tag_number(text)
    if tagged is not None:
        return tagged, "result_tag"
    return numbers[0], "result_tag_fallback_first"


def snippet(text: str, max_len: int = 180) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= max_len:
        return compact
    return compact[: max_len - 3] + "..."


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

    precision = resolve_numeric_tolerance(raw_config, resolved, logger)
    normalize_mode = get_path(resolved, "eval.numeric.normalize_percent_mode", "auto")
    extract_strategy = resolve_extract_strategy(raw_config, resolved, logger)
    write_per_query = bool(get_path(resolved, "eval.numeric.write_per_query", True))
    logger.info("write_numeric_per_query=%s", write_per_query)

    per_query_path = os.path.join(run_dir, "numeric_per_query.jsonl")
    em_list: List[int] = []
    abs_errors: List[float] = []
    rel_errors: List[float] = []

    missing_pred = 0
    missing_gold = 0
    multi_pred = 0
    multi_gold = 0
    fallback_reason_counts: Counter[str] = Counter()
    calc_skip_reason_counts: Counter[str] = Counter()
    calc_used_count = 0
    fallback_count = 0
    calc_used_em_all: List[int] = []
    fallback_em_all: List[int] = []
    calc_used_em_on_covered: List[int] = []
    fallback_em_on_covered: List[int] = []
    calc_used_covered_count = 0
    fallback_covered_count = 0
    needs_calc_count = 0
    needs_calc_known_count = 0

    per_query_file = open(per_query_path, "w", encoding="utf-8") if write_per_query else None
    try:
        for rec in records:
            qid = rec.get("qid")
            gold = rec.get("answer", "")
            pred_row = preds.get(qid, {}) if qid in preds else {}
            pred = pred_row.get("pred_answer", "")
            fallback_reason = pred_row.get("fallback_reason")
            calc_skip_reason = pred_row.get("calc_skip_reason")
            calc_skip_detail = pred_row.get("calc_skip_detail")
            needs_calc = pred_row.get("needs_calc")
            calculator_used_raw = pred_row.get("calculator_used")

            calculator_used: bool
            if qid not in preds:
                fallback_reason = "missing_prediction_row"
                calculator_used = False
            elif isinstance(calculator_used_raw, bool):
                calculator_used = calculator_used_raw
            elif isinstance(calculator_used_raw, (int, float)):
                calculator_used = bool(calculator_used_raw)
            else:
                calculator_used = fallback_reason in {None, ""}

            is_fallback = not calculator_used
            if is_fallback and fallback_reason in {None, ""}:
                fallback_reason = calc_skip_detail or calc_skip_reason or "fallback"
            if is_fallback:
                fallback_count += 1
                fallback_reason_counts[str(fallback_reason)] += 1
                if calc_skip_reason not in {None, ""}:
                    calc_skip_reason_counts[str(calc_skip_reason)] += 1
            else:
                calc_used_count += 1
            if isinstance(needs_calc, bool):
                needs_calc_known_count += 1
                if needs_calc:
                    needs_calc_count += 1

            gold_nums = extract_numbers(gold)
            pred_nums = extract_numbers(pred)

            if len(gold_nums) > 1:
                multi_gold += 1
            if len(pred_nums) > 1:
                multi_pred += 1

            gold_val, gold_strategy_used = pick_number(gold, gold_nums, extract_strategy)
            pred_val, pred_strategy_used = pick_number(pred, pred_nums, extract_strategy)

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

            if is_fallback:
                fallback_em_all.append(em)
                if extracted_ok:
                    fallback_covered_count += 1
                    fallback_em_on_covered.append(em)
            else:
                calc_used_em_all.append(em)
                if extracted_ok:
                    calc_used_covered_count += 1
                    calc_used_em_on_covered.append(em)

            if per_query_file is not None:
                per_query_file.write(
                    json.dumps(
                        {
                            "qid": qid,
                            "gold_number": gold_val["value"] if gold_val is not None else None,
                            "pred_number": pred_val["value"] if pred_val is not None else None,
                            "gold_num": gold_val["value"] if gold_val is not None else None,
                            "pred_num": pred_val["value"] if pred_val is not None else None,
                            "strategy_used": pred_strategy_used,
                            "gold_strategy_used": gold_strategy_used,
                            "extract_strategy": extract_strategy,
                            "em": em,
                            "numeric_em": em,
                            "abs_err": abs_err,
                            "rel_err": rel_err,
                            "extracted_ok": extracted_ok,
                            "fallback_reason": fallback_reason,
                            "calc_route": "fallback" if is_fallback else "calc_used",
                            "calculator_used": calculator_used,
                            "calc_skip_reason": calc_skip_reason,
                            "calc_skip_detail": calc_skip_detail,
                            "needs_calc": needs_calc,
                            "pred_text_snippet": snippet(pred),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
    finally:
        if per_query_file is not None:
            per_query_file.close()

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
        "extract_strategy": extract_strategy,
        "write_per_query": write_per_query,
        "fallback_ratio": fallback_count / len(records) if records else 0.0,
        "calc_used_ratio": calc_used_count / len(records) if records else 0.0,
        "calc_used_em": mean(calc_used_em_all) if calc_used_em_all else 0.0,
        "fallback_em": mean(fallback_em_all) if fallback_em_all else 0.0,
        "gap_vs_fallback": (
            (mean(calc_used_em_all) if calc_used_em_all else 0.0)
            - (mean(fallback_em_all) if fallback_em_all else 0.0)
        ),
        "fallback_reason_counts": dict(fallback_reason_counts),
        "calc_skip_reason_counts": dict(calc_skip_reason_counts),
        "needs_calc_count": needs_calc_count,
        "needs_calc_known_count": needs_calc_known_count,
        "needs_calc_ratio": (
            needs_calc_count / needs_calc_known_count if needs_calc_known_count else None
        ),
        "calc_used": {
            "count": calc_used_count,
            "coverage": calc_used_covered_count / calc_used_count if calc_used_count else 0.0,
            "em_all": mean(calc_used_em_all) if calc_used_em_all else 0.0,
            "em_on_covered": mean(calc_used_em_on_covered) if calc_used_em_on_covered else 0.0,
        },
        "fallback": {
            "count": fallback_count,
            "coverage": fallback_covered_count / fallback_count if fallback_count else 0.0,
            "em_all": mean(fallback_em_all) if fallback_em_all else 0.0,
            "em_on_covered": mean(fallback_em_on_covered) if fallback_em_on_covered else 0.0,
        },
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
