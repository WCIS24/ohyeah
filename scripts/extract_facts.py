from __future__ import annotations

import argparse
import json
import os
import random
import sys
from typing import Any, Dict, List, Optional

import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from calculator.extract import extract_facts_from_text  # noqa: E402
from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402
from training.pairs import load_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract numeric facts from evidence")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--results", default=None, help="retrieval_results.jsonl")
    parser.add_argument("--subset-qids", default=None, help="subset qids path")
    return parser.parse_args()


def apply_overrides(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    if args.results is not None:
        config["results_path"] = args.results
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
    results_path = config.get("results_path")
    if not results_path or not os.path.exists(results_path):
        logger.error("missing results_path: %s", results_path)
        return 2
    logger.info("results_path=%s subset_qids_path=%s", results_path, config.get("subset_qids_path"))

    records = load_jsonl(dev_path)
    results = {r["qid"]: r for r in load_jsonl(results_path)}

    subset_qids = load_subset(config.get("subset_qids_path"))
    if subset_qids:
        records = [r for r in records if r.get("qid") in subset_qids]

    facts_path = os.path.join(run_dir, "facts.jsonl")
    total_facts = 0
    inferred_year = 0
    missing_year = 0
    missing_unit = 0
    queries_with_facts = 0

    with open(facts_path, "w", encoding="utf-8") as f:
        for rec in records:
            qid = rec.get("qid")
            query = rec.get("query", "")
            res = results.get(qid)
            if not res:
                continue
            chunks = res.get("all_collected_chunks") or res.get("final_top_chunks") or []
            year_candidates = None

            qid_facts = []
            for ch in chunks:
                chunk_id = ch.get("chunk_id")
                text = ch.get("text", "")
                if not text:
                    continue
                facts = extract_facts_from_text(qid, chunk_id, text, query, year_candidates)
                qid_facts.extend(facts)

            for fact in qid_facts:
                f.write(json.dumps(fact.__dict__, ensure_ascii=False) + "\n")

            if qid_facts:
                queries_with_facts += 1
            for fact in qid_facts:
                total_facts += 1
                if fact.inferred_year:
                    inferred_year += 1
                if fact.year is None:
                    missing_year += 1
                if fact.unit is None:
                    missing_unit += 1

    extract_stats = {
        "total_queries": len(records),
        "queries_with_facts": queries_with_facts,
        "no_fact_ratio": 1.0 - (queries_with_facts / len(records)) if records else 0.0,
        "total_facts": total_facts,
        "facts_per_query": total_facts / len(records) if records else 0.0,
        "inferred_year_ratio": inferred_year / total_facts if total_facts else 0.0,
        "missing_year_ratio": missing_year / total_facts if total_facts else 0.0,
        "missing_unit_ratio": missing_unit / total_facts if total_facts else 0.0,
    }

    stats_path = os.path.join(run_dir, "extract_stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(extract_stats, f, indent=2)

    config_out = os.path.join(run_dir, "config.yaml")
    save_config(config, config_out)

    logger.info("extract_stats=%s", extract_stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
