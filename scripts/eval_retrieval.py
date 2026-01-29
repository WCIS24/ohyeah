from __future__ import annotations

import argparse
import json
import os
import random
import sys
from typing import Any, Dict, List, Optional


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402
import numpy as np  # noqa: E402
from retrieval.eval_utils import compute_retrieval_metrics  # noqa: E402
from retrieval.retriever import HybridRetriever  # noqa: E402
from config.schema import (  # noqa: E402
    get_path,
    resolve_config,
    validate_config,
    validate_paths,
    write_resolved_config,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate retrieval")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--split", default=None, help="Override split")
    parser.add_argument("--subset-qids", default=None, help="Optional subset qid list")
    return parser.parse_args()


def apply_overrides(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    if args.split is not None:
        config["eval_split"] = args.split
    if args.subset_qids is not None:
        config["subset_qids_path"] = args.subset_qids
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
    random.seed(seed)
    np.random.seed(seed)
    logger.info("seed=%d", seed)

    processed_dir = get_path(resolved, "data.processed_dir", "data/processed")
    eval_split = raw_config.get("eval_split", "dev")
    eval_file = get_path(resolved, f"data.splits.{eval_split}", f"{eval_split}.jsonl")
    eval_path = os.path.join(processed_dir, eval_file)
    corpus_dir = get_path(resolved, "data.corpus_dir", "data/corpus")
    corpus_file = get_path(resolved, "data.corpus_file", "chunks.jsonl")
    corpus_path = os.path.join(corpus_dir, corpus_file)

    if not os.path.exists(eval_path):
        logger.error("missing eval split: %s", eval_path)
        return 2
    if not os.path.exists(corpus_path):
        logger.error("missing corpus file: %s", corpus_path)
        return 3

    eval_records = load_jsonl(eval_path)
    subset_qids = load_subset(raw_config.get("subset_qids_path"))
    if subset_qids:
        eval_records = [r for r in eval_records if r.get("qid") in subset_qids]
    corpus_chunks = load_jsonl(corpus_path)

    retriever_cfg = resolved.get("retriever", {})
    retriever = HybridRetriever(
        model_name=get_path(resolved, "retriever.dense.model_name_or_path"),
        use_faiss=bool(get_path(resolved, "retriever.index.use_faiss", True)),
        device=retriever_cfg.get("device"),
        batch_size=int(retriever_cfg.get("batch_size", 32)),
    )
    retriever.build_index(corpus_chunks)

    k_values = [int(k) for k in get_path(resolved, "eval.k_list", [1, 5, 10])]
    mode = get_path(resolved, "retriever.mode", "hybrid")
    alpha = float(get_path(resolved, "retriever.hybrid.alpha", 0.5))
    chunk_size = int(get_path(resolved, "chunking.chunk_size", 0))
    overlap = int(get_path(resolved, "chunking.overlap", 0))
    logger.info(
        "dense_model=%s mode=%s alpha=%.3f chunk_size=%d overlap=%d",
        retriever.loaded_model_name,
        mode,
        alpha,
        chunk_size,
        overlap,
    )
    metrics, per_query = compute_retrieval_metrics(
        eval_records=eval_records,
        retriever=retriever,
        k_values=k_values,
        mode=mode,
        alpha=alpha,
    )

    metrics_path = os.path.join(run_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    per_query_path = os.path.join(run_dir, "per_query_results.jsonl")
    with open(per_query_path, "w", encoding="utf-8") as f:
        for row in per_query:
            f.write(json.dumps(row) + "\n")

    with open(os.path.join(run_dir, "git_commit.txt"), "w", encoding="utf-8") as f:
        f.write(f"{git_hash}\n")

    config_out = os.path.join(run_dir, "config.yaml")
    save_config(resolved, config_out)

    logger.info("eval_split=%s subset_qids=%s", eval_split, raw_config.get("subset_qids_path"))
    logger.info("corpus_file=%s", corpus_path)
    logger.info("metrics=%s", metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
