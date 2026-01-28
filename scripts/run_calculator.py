from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from calculator.compute import CalcResult, CalcTrace, compute_for_query  # noqa: E402
from calculator.extract import Fact  # noqa: E402
from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402
from training.pairs import load_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run calculator on extracted facts")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--facts", default=None, help="Override facts.jsonl path")
    parser.add_argument("--subset-qids", default=None, help="Optional subset qids path")
    return parser.parse_args()


def apply_overrides(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    if args.facts is not None:
        config["facts_path"] = args.facts
    if args.subset_qids is not None:
        config["subset_qids_path"] = args.subset_qids
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


def fact_from_dict(data: Dict[str, Any]) -> Fact:
    return Fact(**data)


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

    seed = int(config.get("seed", 42))
    random.seed(seed)
    np.random.seed(seed)
    logger.info("seed=%d", seed)

    dev_path = config.get("processed_dev_path", "data/processed/dev.jsonl")
    facts_path = config.get("facts_path")
    if not facts_path or not os.path.exists(facts_path):
        logger.error("missing facts_path: %s", facts_path)
        return 2
    logger.info("facts_path=%s subset_qids_path=%s", facts_path, config.get("subset_qids_path"))

    records = load_jsonl(dev_path)
    subset_qids = load_subset(config.get("subset_qids_path"))
    if subset_qids:
        records = [r for r in records if r.get("qid") in subset_qids]

    facts_by_qid: Dict[str, List[Fact]] = defaultdict(list)
    for row in load_jsonl(facts_path):
        qid = row.get("qid")
        if not qid:
            continue
        try:
            facts_by_qid[qid].append(fact_from_dict(row))
        except TypeError:
            continue

    results_path = os.path.join(run_dir, "results_R.jsonl")
    traces_path = os.path.join(run_dir, "calc_traces.jsonl")

    status_counts: Counter[str] = Counter()
    task_counts: Counter[str] = Counter()

    output_percent = bool(config.get("output_percent", True))

    with open(results_path, "w", encoding="utf-8") as results_f, open(
        traces_path, "w", encoding="utf-8"
    ) as traces_f:
        for rec in records:
            qid = rec.get("qid")
            query = rec.get("query", "")
            facts = facts_by_qid.get(qid, [])
            result, trace = compute_for_query(query, facts, output_percent)
            result.qid = qid
            trace.qid = qid
            status_counts[result.status] += 1
            task_counts[result.task_type] += 1

            results_f.write(json.dumps(result.__dict__, ensure_ascii=False) + "\n")
            traces_f.write(json.dumps(trace.__dict__, ensure_ascii=False) + "\n")

    total = len(records)
    ok = status_counts.get("ok", 0)
    calc_stats = {
        "total_queries": total,
        "ok_ratio": ok / total if total else 0.0,
        "status_counts": dict(status_counts),
        "task_counts": dict(task_counts),
        "results_path": results_path,
        "traces_path": traces_path,
    }

    stats_path = os.path.join(run_dir, "calc_stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(calc_stats, f, indent=2)

    config_out = os.path.join(run_dir, "config.yaml")
    save_config(config, config_out)

    logger.info("calc_stats=%s", calc_stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
