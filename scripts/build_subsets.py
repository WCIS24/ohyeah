from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402
from training.pairs import load_jsonl  # noqa: E402

YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
ABBREV_RE = re.compile(r"\b[A-Z]{2,6}\b")
PERCENT_RE = re.compile(r"%")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build dev subsets")
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

    processed_path = config.get("processed_dev_path", "data/processed/dev.jsonl")
    subsets_dir = config.get("subsets_dir", "data/subsets")
    ensure_dir(subsets_dir)

    keywords = [k.lower() for k in config.get("complex_keywords", [])]

    records = load_jsonl(processed_path)
    complex_ids = []
    abbrev_ids = []

    rule_hits = {
        "multi_evidence": 0,
        "two_years": 0,
        "compare_keywords": 0,
        "digit_and_year": 0,
        "abbrev": 0,
    }

    for rec in records:
        qid = rec.get("qid")
        query = rec.get("query", "")
        evidences = rec.get("evidences", [])

        has_multi_evidence = len(evidences) >= 2
        years = YEAR_RE.findall(query)
        has_two_years = len({y for y in years}) >= 2
        has_compare = any(k in query.lower() for k in keywords)
        has_digit_year = bool(YEAR_RE.search(query) and (PERCENT_RE.search(query) or re.search(r"\d", query)))

        is_complex = has_multi_evidence or has_two_years or has_compare or has_digit_year
        if is_complex:
            complex_ids.append(qid)

        if has_multi_evidence:
            rule_hits["multi_evidence"] += 1
        if has_two_years:
            rule_hits["two_years"] += 1
        if has_compare:
            rule_hits["compare_keywords"] += 1
        if has_digit_year:
            rule_hits["digit_and_year"] += 1

        if ABBREV_RE.search(query):
            abbrev_ids.append(qid)
            rule_hits["abbrev"] += 1

    complex_path = os.path.join(subsets_dir, "dev_complex_qids.txt")
    with open(complex_path, "w", encoding="utf-8") as f:
        for qid in complex_ids:
            f.write(f"{qid}\n")

    abbrev_path = os.path.join(subsets_dir, "dev_abbrev_qids.txt")
    with open(abbrev_path, "w", encoding="utf-8") as f:
        for qid in abbrev_ids:
            f.write(f"{qid}\n")

    stats = {
        "total": len(records),
        "complex_size": len(complex_ids),
        "complex_ratio": len(complex_ids) / len(records) if records else 0.0,
        "abbrev_size": len(abbrev_ids),
        "abbrev_ratio": len(abbrev_ids) / len(records) if records else 0.0,
        "rule_hits": rule_hits,
        "complex_path": complex_path,
        "abbrev_path": abbrev_path,
    }

    stats_path = os.path.join(run_dir, "subsets_stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    config_out = os.path.join(run_dir, "config.yaml")
    save_config(config, config_out)

    logger.info("stats=%s", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
