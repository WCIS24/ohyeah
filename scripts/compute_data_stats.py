from __future__ import annotations

import argparse
import json
import os
import random
import sys
from typing import Any, Dict

import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge dataset stats and subset stats")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--data-stats", default=None, help="Path to data_stats.json")
    parser.add_argument("--subsets-stats", default=None, help="Path to subsets_stats.json")
    parser.add_argument("--output", default=None, help="Output path for merged stats JSON")
    parser.add_argument("--run-id", default=None, help="Override run_id")
    return parser.parse_args()


def apply_overrides(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    if args.data_stats is not None:
        config["data_stats_path"] = args.data_stats
    if args.subsets_stats is not None:
        config["subsets_stats_path"] = args.subsets_stats
    if args.output is not None:
        config["output_path"] = args.output
    if args.run_id is not None:
        config["run_id"] = args.run_id
    return config


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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

    seed = int(config.get("seed", 42))
    random.seed(seed)
    np.random.seed(seed)

    git_hash = get_git_hash()
    config["git_hash"] = git_hash
    logger.info("seed=%d git_hash=%s", seed, git_hash)

    data_stats_path = config.get("data_stats_path")
    subsets_stats_path = config.get("subsets_stats_path")
    output_path = config.get("output_path", "docs/data_stats.json")

    if not data_stats_path or not os.path.exists(data_stats_path):
        logger.error("missing data_stats_path: %s", data_stats_path)
        return 2
    if not subsets_stats_path or not os.path.exists(subsets_stats_path):
        logger.error("missing subsets_stats_path: %s", subsets_stats_path)
        return 3

    data_stats = load_json(data_stats_path)
    subsets_stats = load_json(subsets_stats_path)

    merged: Dict[str, Any] = {
        "source": {
            "data_stats_path": data_stats_path,
            "subsets_stats_path": subsets_stats_path,
            "generated_by": "scripts/compute_data_stats.py",
            "git_hash": git_hash,
        },
        "totals": {
            "total_queries": data_stats.get("query_length", {}).get("count"),
            "dev_total": subsets_stats.get("total"),
        },
        "splits": data_stats.get("splits"),
        "query_length": data_stats.get("query_length"),
        "evidence_count": data_stats.get("evidence_count"),
        "query_flags": data_stats.get("query_flags"),
        "dev_subsets": {
            "complex": {
                "size": subsets_stats.get("complex_size"),
                "ratio": subsets_stats.get("complex_ratio"),
                "rule_hits": subsets_stats.get("rule_hits"),
                "path": subsets_stats.get("complex_path"),
            },
            "abbrev": {
                "size": subsets_stats.get("abbrev_size"),
                "ratio": subsets_stats.get("abbrev_ratio"),
                "path": subsets_stats.get("abbrev_path"),
            },
        },
    }

    ensure_dir(os.path.dirname(output_path))
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    metrics_path = os.path.join(run_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    config_out = os.path.join(run_dir, "config.yaml")
    save_config(config, config_out)

    with open(os.path.join(run_dir, "git_commit.txt"), "w", encoding="utf-8") as f:
        f.write(f"{git_hash}\n")

    logger.info("data_stats_path=%s", data_stats_path)
    logger.info("subsets_stats_path=%s", subsets_stats_path)
    logger.info("output_path=%s", output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
