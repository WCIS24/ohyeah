from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from typing import Dict

import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402
from training.pairs import load_jsonl  # noqa: E402

NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
KEYWORDS = [
    "percent",
    "percentage",
    "yoy",
    "growth",
    "increase",
    "decrease",
    "difference",
    "change",
    "times",
    "同比",
    "增速",
    "增长率",
    "增长",
    "下降",
    "差值",
    "变化",
    "增减",
    "占比",
    "比例",
    "倍",
    "倍数",
]
PERCENT_RE = re.compile(r"%")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build numeric subset")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    return parser.parse_args()


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

    records = load_jsonl(processed_path)

    stats = {
        "total": len(records),
        "rule_hits": {"query_number": 0, "answer_number": 0, "keyword": 0, "percent": 0},
        "query_only": 0,
        "answer_only": 0,
        "both": 0,
    }

    numeric_qids = []

    for rec in records:
        qid = rec.get("qid")
        query = rec.get("query", "")
        answer = rec.get("answer", "")

        query_num = bool(NUMBER_RE.search(query))
        answer_num = bool(NUMBER_RE.search(answer))
        keyword_hit = any(k in query.lower() for k in KEYWORDS)
        percent_hit = bool(PERCENT_RE.search(query))

        if query_num:
            stats["rule_hits"]["query_number"] += 1
        if answer_num:
            stats["rule_hits"]["answer_number"] += 1
        if keyword_hit:
            stats["rule_hits"]["keyword"] += 1
        if percent_hit:
            stats["rule_hits"]["percent"] += 1

        is_numeric = query_num or answer_num or keyword_hit or percent_hit
        if is_numeric:
            numeric_qids.append(qid)

        if query_num and answer_num:
            stats["both"] += 1
        elif query_num:
            stats["query_only"] += 1
        elif answer_num:
            stats["answer_only"] += 1

    subset_path = os.path.join(subsets_dir, "dev_numeric_qids.txt")
    with open(subset_path, "w", encoding="utf-8") as f:
        for qid in numeric_qids:
            f.write(f"{qid}\n")

    stats["numeric_size"] = len(numeric_qids)
    stats["numeric_ratio"] = len(numeric_qids) / len(records) if records else 0.0
    stats["subset_path"] = subset_path

    stats_path = os.path.join(run_dir, "numeric_subset_stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    config_out = os.path.join(run_dir, "config.yaml")
    save_config(config, config_out)

    logger.info("stats=%s", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
