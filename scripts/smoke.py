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
from finder_rag.data import build_corpus, build_records, load_finder_csv  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.metrics import exact_match, mean, recall_at_k  # noqa: E402
from finder_rag.retrieval import TfidfRetriever  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FinDER RAG smoke test")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--run-id", default=None, help="Override run_id")
    parser.add_argument("--seed", type=int, default=None, help="Override seed")
    parser.add_argument("--subset-size", type=int, default=None, help="Override subset size")
    parser.add_argument("--k", type=int, default=None, help="Override recall@k")
    parser.add_argument("--finder-csv", default=None, help="Override dataset path")
    parser.add_argument("--output-dir", default=None, help="Override output dir")
    return parser.parse_args()


def apply_overrides(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    if args.run_id is not None:
        config["run_id"] = args.run_id
    if args.seed is not None:
        config["seed"] = args.seed
    if args.subset_size is not None:
        config["subset_size"] = args.subset_size
    if args.k is not None:
        config["k"] = args.k
    if args.finder_csv is not None:
        config["finder_csv"] = args.finder_csv
    if args.output_dir is not None:
        config["output_dir"] = args.output_dir
    return config


def placeholder_generate(evidence: str) -> str:
    snippet = evidence.replace("\n", " ").strip()
    return f"Answer based on evidence: {snippet[:200]}"


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

    finder_csv = config.get("finder_csv")
    if not finder_csv or not os.path.exists(finder_csv):
        logger.error("finder_csv not found: %s", finder_csv)
        return 2

    df = load_finder_csv(finder_csv)
    records = build_records(df, max_evidence_per_query=int(config.get("max_evidence_per_query", 3)))

    if not records:
        logger.error("no valid records found in dataset")
        return 3

    subset_size = int(config.get("subset_size", 20))
    if subset_size <= 0:
        subset_size = 20

    if subset_size < len(records):
        records = random.sample(records, subset_size)

    corpus = build_corpus(records)
    logger.info("finder_csv=%s subset_size=%d k=%d", finder_csv, len(records), int(config.get("k", 5)))
    logger.info("records=%d corpus=%d", len(records), len(corpus))

    retriever_cfg = config.get("retriever", {})
    retriever = TfidfRetriever(
        max_features=int(retriever_cfg.get("max_features", 20000)),
        ngram_range=tuple(retriever_cfg.get("ngram_range", [1, 2])),
    )
    retriever.fit(corpus)

    k = int(config.get("k", 5))
    recall_scores = []
    em_scores = []

    for rec in records:
        query = rec["query"]
        evidence_list = rec["evidence"]
        indices = retriever.retrieve(query, k=k)
        retrieved = [corpus[i] for i in indices]
        recall_scores.append(recall_at_k(retrieved, evidence_list, k=k))

        pred = placeholder_generate(retrieved[0]) if retrieved else ""
        em_scores.append(exact_match(pred, rec["answer"]))

    metrics = {
        "recall_at_k": mean(recall_scores),
        "exact_match": mean(em_scores),
        "num_queries": len(records),
        "k": k,
        "seed": seed,
    }

    config_out = os.path.join(run_dir, "config.yaml")
    metrics_out = os.path.join(run_dir, "metrics.json")

    save_config(config, config_out)
    with open(metrics_out, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    logger.info("metrics=%s", metrics)
    logger.info("run_dir=%s", run_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
