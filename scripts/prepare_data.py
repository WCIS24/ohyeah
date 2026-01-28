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

from data.finder import (  # noqa: E402
    compute_query_flags,
    dataset_to_records,
    inspect_schema,
    load_finder_dataset,
    split_dataset,
    summarize_numeric,
    summarize_text_stats,
    write_json,
)
from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare FinDER data")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--out-dir", default=None, help="Override output dir")
    parser.add_argument("--max-samples", type=int, default=None, help="Override max samples")
    parser.add_argument("--seed", type=int, default=None, help="Override seed")
    return parser.parse_args()


def apply_overrides(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    if args.out_dir is not None:
        config["processed_dir"] = args.out_dir
    if args.max_samples is not None:
        config["max_samples"] = args.max_samples
    if args.seed is not None:
        config["seed"] = args.seed
    return config


def validate_fields(fields: Dict[str, str], available: Dict[str, Any]) -> None:
    for key, value in fields.items():
        if value is None:
            continue
        if value not in available:
            raise KeyError(f"Field '{value}' (for {key}) not in dataset columns: {list(available)}")


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

    dataset_name = config.get("dataset_name")
    dataset_config = config.get("dataset_config")
    data_files = config.get("data_files")
    if not data_files:
        data_files = config.get("finder_csv")

    dataset = load_finder_dataset(
        dataset_name=dataset_name,
        dataset_config=dataset_config,
        data_files=data_files,
    )

    schema = inspect_schema(dataset)
    schema_path = os.path.join(run_dir, "data_schema.json")
    write_json(schema, schema_path)

    train_ratio = float(config.get("train_ratio", 0.8))
    dev_ratio = float(config.get("dev_ratio", 0.1))
    test_ratio = float(config.get("test_ratio", 0.1))
    max_samples = config.get("max_samples")
    if max_samples is not None:
        max_samples = int(max_samples)

    dataset = split_dataset(
        dataset,
        seed=seed,
        train_ratio=train_ratio,
        dev_ratio=dev_ratio,
        test_ratio=test_ratio,
        max_samples=max_samples,
    )

    field_map = config.get("field_map", {})
    example_split = next(iter(dataset.keys()))
    available_fields = dataset[example_split].features
    validate_fields(field_map, available_fields)

    processed_dir = config.get("processed_dir", "data/processed")
    ensure_dir(processed_dir)

    stats = {"splits": {}, "query_length": {}, "evidence_count": {}, "query_flags": {}}
    all_queries = []
    evidence_counts = []

    for split_name, split_data in dataset.items():
        records = dataset_to_records(split_data, field_map)
        stats["splits"][split_name] = len(records)
        output_path = os.path.join(processed_dir, f"{split_name}.jsonl")
        with open(output_path, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                all_queries.append(rec["query"])
                evidence_counts.append(len(rec["evidences"]))

    stats["query_length"] = summarize_text_stats(all_queries)
    stats["evidence_count"] = summarize_numeric(evidence_counts)
    stats["query_flags"] = compute_query_flags(all_queries)

    data_stats_path = os.path.join(run_dir, "data_stats.json")
    write_json(stats, data_stats_path)

    config_out = os.path.join(run_dir, "config.yaml")
    save_config(config, config_out)

    logger.info("processed_dir=%s", processed_dir)
    logger.info("stats=%s", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
