from __future__ import annotations

import argparse
import json
import os
import random
import sys
from typing import Any, Dict, List, Tuple

import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402
from retrieval.retriever import HybridRetriever  # noqa: E402
from training.mining import build_bm25, mine_bm25, select_hard_negs  # noqa: E402
from training.pairs import build_corpus_index, build_training_pairs, load_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mine hard negatives")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    return parser.parse_args()


def load_corpus(path: str) -> List[Dict[str, Any]]:
    return load_jsonl(path)


def mine_dense(
    query: str,
    retriever: HybridRetriever,
    top_n: int,
) -> List[Tuple[int, float]]:
    results = retriever.retrieve(query, top_k=top_n, mode="dense", alpha=0.0)
    indices = []
    for res in results:
        chunk_id = res.get("meta", {}).get("chunk_id")
        indices.append((chunk_id, float(res.get("dense", res.get("score", 0.0)))))
    return indices


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

    seed = int(config.get("seed", 42))
    random.seed(seed)
    np.random.seed(seed)
    git_hash = get_git_hash()
    config["git_hash"] = git_hash
    logger.info("seed=%d git_hash=%s", seed, git_hash)

    processed_train_path = config.get("processed_train_path", "data/processed/train.jsonl")
    corpus_path = config.get("corpus_path", "data/corpus/chunks.jsonl")
    top_n = int(config.get("top_n", 50))
    hard_k = int(config.get("hard_k", 5))
    strategy = config.get("strategy", "bm25")
    max_samples = config.get("max_samples")

    train_records = load_jsonl(processed_train_path)
    corpus_chunks = load_corpus(corpus_path)
    corpus_index = build_corpus_index(corpus_chunks)

    pairs, pos_stats = build_training_pairs(train_records, corpus_index)
    if max_samples:
        pairs = pairs[: int(max_samples)]

    logger.info("pairs=%d pos_stats=%s", len(pairs), pos_stats)

    hard_negs_output = []
    missing_negs = 0
    total_negs = 0

    if strategy == "bm25":
        bm25 = build_bm25(corpus_chunks)
        for pair in pairs:
            pos_chunk_id = pair["pos_chunk_id"]
            candidates = mine_bm25(pair["query"], bm25, corpus_chunks, top_n)
            negs = select_hard_negs(candidates, corpus_chunks, pos_chunk_id, hard_k)
            if not negs:
                missing_negs += 1
            total_negs += len(negs)
            hard_negs_output.append(
                {
                    "qid": pair["qid"],
                    "query": pair["query"],
                    "pos_chunk_id": pos_chunk_id,
                    "pos_text": pair["pos_text"],
                    "hard_negs": negs,
                }
            )
    elif strategy == "dense":
        retriever_cfg = config.get("retriever", {})
        retriever = HybridRetriever(
            model_name=retriever_cfg.get("model_name", "sentence-transformers/all-MiniLM-L6-v2"),
            use_faiss=bool(retriever_cfg.get("use_faiss", False)),
            device=retriever_cfg.get("device"),
            batch_size=int(retriever_cfg.get("batch_size", 32)),
        )
        retriever.build_index(corpus_chunks)
        chunk_by_id = {c.get("meta", {}).get("chunk_id"): c for c in corpus_chunks}
        for pair in pairs:
            pos_chunk_id = pair["pos_chunk_id"]
            candidates = retriever.retrieve(pair["query"], top_k=top_n, mode="dense", alpha=0.0)
            negs = []
            for res in candidates:
                chunk_id = res.get("meta", {}).get("chunk_id")
                if chunk_id == pos_chunk_id:
                    continue
                chunk = chunk_by_id.get(chunk_id)
                if not chunk:
                    continue
                negs.append(
                    {
                        "chunk_id": chunk_id,
                        "text": chunk.get("text"),
                        "score": float(res.get("dense", res.get("score", 0.0))),
                    }
                )
                if len(negs) >= hard_k:
                    break
            if not negs:
                missing_negs += 1
            total_negs += len(negs)
            hard_negs_output.append(
                {
                    "qid": pair["qid"],
                    "query": pair["query"],
                    "pos_chunk_id": pos_chunk_id,
                    "pos_text": pair["pos_text"],
                    "hard_negs": negs,
                }
            )
    else:
        logger.error("unsupported strategy: %s", strategy)
        return 2

    output_path = config.get("output_path", "data/processed/train_triplets.jsonl")
    ensure_dir(os.path.dirname(output_path))
    with open(output_path, "w", encoding="utf-8") as f:
        for row in hard_negs_output:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    stats = {
        "total_samples": len(hard_negs_output),
        "avg_hard_negs": (total_negs / len(hard_negs_output)) if hard_negs_output else 0.0,
        "missing_hard_neg_ratio": (missing_negs / len(hard_negs_output))
        if hard_negs_output
        else 0.0,
        "pos_text_fallback_ratio": pos_stats.get("pos_text_fallback", 0)
        / max(pos_stats.get("pos_found", 1), 1),
        "pos_missing_ratio": pos_stats.get("pos_missing", 0) / max(pos_stats.get("total", 1), 1),
        "strategy": strategy,
        "top_n": top_n,
        "hard_k": hard_k,
    }

    stats_path = os.path.join(run_dir, "neg_mining_stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    config_out = os.path.join(run_dir, "config.yaml")
    save_config(config, config_out)

    logger.info("output_path=%s", output_path)
    logger.info("stats=%s", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
