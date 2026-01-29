from __future__ import annotations

import argparse
import json
import os
import random
import sys
from typing import Any, Dict, List

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402
from retrieval.retriever import HybridRetriever  # noqa: E402
import numpy as np  # noqa: E402
from config.schema import get_path, resolve_config, validate_config, validate_paths, write_resolved_config  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run baseline RAG")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--split", default=None, help="Override split")
    return parser.parse_args()


def apply_overrides(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    if args.split is not None:
        config["eval_split"] = args.split
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


def placeholder_generate(query: str, chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return "No evidence found."
    snippet = chunks[0]["text"].replace("\n", " ").strip()
    return f"Q: {query}\nAnswer (template): {snippet[:200]}"


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
    corpus_chunks = load_jsonl(corpus_path)

    retriever_cfg = resolved.get("retriever", {})
    retriever = HybridRetriever(
        model_name=get_path(resolved, "retriever.dense.model_name_or_path"),
        use_faiss=bool(get_path(resolved, "retriever.index.use_faiss", True)),
        device=retriever_cfg.get("device"),
        batch_size=int(retriever_cfg.get("batch_size", 32)),
    )
    retriever.build_index(corpus_chunks)

    k = int(get_path(resolved, "retriever.top_k", 5))
    mode = get_path(resolved, "retriever.mode", "hybrid")
    alpha = float(get_path(resolved, "retriever.hybrid.alpha", 0.5))
    chunk_size = int(get_path(resolved, "chunking.chunk_size", 0))
    overlap = int(get_path(resolved, "chunking.overlap", 0))
    logger.info(
        "dense_model=%s mode=%s alpha=%.3f top_k=%d chunk_size=%d overlap=%d",
        retriever.loaded_model_name,
        mode,
        alpha,
        k,
        chunk_size,
        overlap,
    )

    predictions_path = os.path.join(run_dir, "predictions.jsonl")
    with open(predictions_path, "w", encoding="utf-8") as f:
        for rec in eval_records:
            query = rec.get("query", "")
            qid = rec.get("qid")
            chunks = retriever.retrieve(query, top_k=k, alpha=alpha, mode=mode)
            used_chunks = [c.get("meta", {}).get("chunk_id") for c in chunks]
            pred = placeholder_generate(query, chunks)
            f.write(
                json.dumps(
                    {"qid": qid, "pred_answer": pred, "used_chunks": used_chunks},
                    ensure_ascii=False,
                )
                + "\n"
            )

    with open(os.path.join(run_dir, "git_commit.txt"), "w", encoding="utf-8") as f:
        f.write(f"{git_hash}\n")

    config_out = os.path.join(run_dir, "config.yaml")
    save_config(resolved, config_out)

    logger.info("predictions_path=%s", predictions_path)
    logger.info("eval_split=%s", eval_split)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
