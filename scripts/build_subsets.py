from __future__ import annotations

import argparse
import json
import os
import re
import random
import sys
from collections import Counter
from typing import Any, Dict, Iterable, List, Tuple

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402
import numpy as np  # noqa: E402
from training.pairs import load_jsonl  # noqa: E402

YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
ABBREV_RE = re.compile(r"\b[A-Z]{2,6}\b")
PERCENT_RE = re.compile(r"%")
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
NUMERIC_KEYWORDS = [
    "percent",
    "percentage",
    "yoy",
    "growth",
    "increase",
    "decrease",
    "difference",
    "change",
    "times",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build dev subsets")
    parser.add_argument(
        "--config",
        default="configs/build_subsets.yaml",
        help="Path to YAML config (default: configs/build_subsets.yaml)",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Override output subset directory (e.g., data/subsets_v2)",
    )
    return parser.parse_args()


def extract_years(text: str) -> List[str]:
    return [m.group(0) for m in YEAR_RE.finditer(text or "")]


def has_two_distinct_years(text: str) -> bool:
    years = extract_years(text)
    return len(set(years)) >= 2


def detect_numeric_query(query: str, answer: str) -> Tuple[bool, Dict[str, bool]]:
    query_lower = query.lower()
    query_num = bool(NUMBER_RE.search(query))
    answer_num = bool(NUMBER_RE.search(answer))
    keyword_hit = any(k in query_lower for k in NUMERIC_KEYWORDS)
    percent_hit = bool(PERCENT_RE.search(query))
    flags = {
        "query_number": query_num,
        "answer_number": answer_num,
        "keyword": keyword_hit,
        "percent": percent_hit,
    }
    return query_num or answer_num or keyword_hit or percent_hit, flags


def write_qid_file(path: str, qids: Iterable[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for qid in qids:
            f.write(f"{qid}\n")


def summarize_year_hist(year_unique_counts: List[int], year_counter: Counter[str]) -> Dict[str, Any]:
    hist = {
        "0": sum(1 for c in year_unique_counts if c == 0),
        "1": sum(1 for c in year_unique_counts if c == 1),
        "2": sum(1 for c in year_unique_counts if c == 2),
        "3_plus": sum(1 for c in year_unique_counts if c >= 3),
    }
    return {
        "unique_year_count_hist": hist,
        "queries_with_years": sum(1 for c in year_unique_counts if c > 0),
        "top_years": year_counter.most_common(10),
    }


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    if args.out_dir:
        config["subsets_dir"] = args.out_dir

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

    keywords = [k.lower() for k in config.get("complex_keywords", [])]

    records = load_jsonl(processed_path)
    complex_ids = []
    abbrev_ids = []
    numeric_ids = []
    year_unique_counts: List[int] = []
    year_counter: Counter[str] = Counter()

    rule_hits = {
        "multi_evidence": 0,
        "two_years": 0,
        "compare_keywords": 0,
        "digit_and_year": 0,
        "abbrev": 0,
        "numeric_query": 0,
        "numeric_answer": 0,
        "numeric_keyword": 0,
        "numeric_percent": 0,
    }

    for rec in records:
        qid = rec.get("qid")
        query = rec.get("query", "")
        answer = rec.get("answer", "")
        evidences = rec.get("evidences", [])

        has_multi_evidence = len(evidences) >= 2
        years = extract_years(query)
        unique_years = sorted(set(years))
        year_unique_counts.append(len(unique_years))
        for year in unique_years:
            year_counter[year] += 1

        has_two_years = len(unique_years) >= 2
        has_compare = any(k in query.lower() for k in keywords)
        has_digit_year = bool(YEAR_RE.search(query) and (PERCENT_RE.search(query) or re.search(r"\d", query)))
        is_numeric, numeric_flags = detect_numeric_query(query, answer)

        is_complex = has_multi_evidence or has_two_years or has_compare or has_digit_year
        if is_complex:
            complex_ids.append(qid)
        if is_numeric:
            numeric_ids.append(qid)

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

        if numeric_flags["query_number"]:
            rule_hits["numeric_query"] += 1
        if numeric_flags["answer_number"]:
            rule_hits["numeric_answer"] += 1
        if numeric_flags["keyword"]:
            rule_hits["numeric_keyword"] += 1
        if numeric_flags["percent"]:
            rule_hits["numeric_percent"] += 1

    complex_path = os.path.join(subsets_dir, "dev_complex_qids.txt")
    abbrev_path = os.path.join(subsets_dir, "dev_abbrev_qids.txt")
    numeric_path = os.path.join(subsets_dir, "dev_numeric_qids.txt")
    write_qid_file(complex_path, complex_ids)
    write_qid_file(abbrev_path, abbrev_ids)
    write_qid_file(numeric_path, numeric_ids)

    stats = {
        "git_hash": git_hash,
        "seed": seed,
        "regex": {
            "year_re": YEAR_RE.pattern,
            "abbrev_re": ABBREV_RE.pattern,
            "number_re": NUMBER_RE.pattern,
        },
        "total": len(records),
        "subset_counts": {
            "complex": len(complex_ids),
            "abbrev": len(abbrev_ids),
            "numeric": len(numeric_ids),
        },
        "complex_size": len(complex_ids),
        "complex_ratio": len(complex_ids) / len(records) if records else 0.0,
        "abbrev_size": len(abbrev_ids),
        "abbrev_ratio": len(abbrev_ids) / len(records) if records else 0.0,
        "numeric_size": len(numeric_ids),
        "numeric_ratio": len(numeric_ids) / len(records) if records else 0.0,
        "year_summary": summarize_year_hist(year_unique_counts, year_counter),
        "rule_hits": rule_hits,
        "complex_path": complex_path,
        "abbrev_path": abbrev_path,
        "numeric_path": numeric_path,
    }

    stats_path = os.path.join(subsets_dir, "subsets_stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    run_stats_path = os.path.join(run_dir, "subsets_stats.json")
    with open(run_stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    config_out = os.path.join(run_dir, "config.yaml")
    save_config(config, config_out)

    logger.info("stats=%s", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
