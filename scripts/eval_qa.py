from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.metrics import exact_match, mean  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate QA predictions")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--predictions", default=None, help="Override predictions file")
    parser.add_argument("--gold", default=None, help="Override gold split file")
    return parser.parse_args()


def apply_overrides(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    if args.predictions is not None:
        config["predictions_file"] = args.predictions
    if args.gold is not None:
        config["gold_file"] = args.gold
    return config


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def tokenize(text: str) -> List[str]:
    return text.lower().split()


def token_f1(pred: str, gold: str) -> float:
    pred_tokens = tokenize(pred)
    gold_tokens = tokenize(gold)
    if not pred_tokens or not gold_tokens:
        return 0.0
    common = {}
    for t in pred_tokens:
        common[t] = common.get(t, 0) + 1
    match = 0
    for t in gold_tokens:
        if common.get(t, 0) > 0:
            match += 1
            common[t] -= 1
    precision = match / len(pred_tokens)
    recall = match / len(gold_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    config = apply_overrides(config, args)

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

    predictions_file = config.get("predictions_file")
    gold_file = config.get("gold_file")
    if not predictions_file or not os.path.exists(predictions_file):
        logger.error("missing predictions file: %s", predictions_file)
        return 2
    if not gold_file or not os.path.exists(gold_file):
        logger.error("missing gold file: %s", gold_file)
        return 3

    predictions = {row["qid"]: row for row in load_jsonl(predictions_file)}
    gold = load_jsonl(gold_file)

    em_scores = []
    f1_scores = []
    missing = 0

    for row in gold:
        qid = row.get("qid")
        if qid not in predictions:
            missing += 1
            continue
        pred = predictions[qid].get("pred_answer", "")
        gold_ans = row.get("answer", "")
        if gold_ans is None or gold_ans == "":
            missing += 1
            continue
        em_scores.append(exact_match(pred, gold_ans))
        f1_scores.append(token_f1(pred, gold_ans))

    metrics = {
        "exact_match": mean(em_scores),
        "token_f1": mean(f1_scores),
        "missing_rate": missing / len(gold) if gold else 0.0,
        "num_samples": len(em_scores),
    }

    metrics_path = os.path.join(run_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    config_out = os.path.join(run_dir, "config.yaml")
    save_config(config, config_out)

    logger.info("metrics=%s", metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
