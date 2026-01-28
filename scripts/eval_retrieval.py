from __future__ import annotations

import argparse
import json
import os
import random
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.metrics import mean, reciprocal_rank  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402
from retrieval.retriever import HybridRetriever  # noqa: E402
import numpy as np  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate retrieval")
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


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def match_chunk(
    chunk: Dict[str, Any],
    qid: str,
    gold_evidences: List[Dict[str, Any]],
) -> Tuple[bool, str, Optional[int]]:
    meta = chunk.get("meta", {})
    evidence_id = meta.get("evidence_id")
    doc_id = meta.get("doc_id")
    source_qid = meta.get("source_qid")

    for ev in gold_evidences:
        ev_id = ev.get("meta", {}).get("evidence_id")
        ev_doc = ev.get("doc_id")
        if source_qid == qid and evidence_id == ev_id:
            if ev_doc is None or doc_id == ev_doc:
                return True, "id", ev_id

    chunk_text = normalize_text(chunk.get("text", ""))
    gold_texts = [normalize_text(ev.get("text", "")) for ev in gold_evidences]
    for ev_text, ev in zip(gold_texts, gold_evidences):
        if not ev_text:
            continue
        if chunk_text in ev_text or ev_text in chunk_text:
            return True, "text", ev.get("meta", {}).get("evidence_id")

    return False, "none", None


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

    processed_dir = config.get("processed_dir", "data/processed")
    eval_split = config.get("eval_split", "dev")
    eval_path = os.path.join(processed_dir, f"{eval_split}.jsonl")
    corpus_file = config.get("corpus_file", "data/corpus/chunks.jsonl")

    if not os.path.exists(eval_path):
        logger.error("missing eval split: %s", eval_path)
        return 2
    if not os.path.exists(corpus_file):
        logger.error("missing corpus file: %s", corpus_file)
        return 3

    eval_records = load_jsonl(eval_path)
    corpus_chunks = load_jsonl(corpus_file)

    retriever_cfg = config.get("retriever", {})
    retriever = HybridRetriever(
        model_name=retriever_cfg.get("model_name", "sentence-transformers/all-MiniLM-L6-v2"),
        use_faiss=bool(retriever_cfg.get("use_faiss", True)),
        device=retriever_cfg.get("device"),
        batch_size=int(retriever_cfg.get("batch_size", 32)),
    )
    retriever.build_index(corpus_chunks)

    k_values = config.get("k_values", [1, 5, 10])
    k_values = [int(k) for k in k_values]
    k_max = max(k_values)
    mode = config.get("mode", "hybrid")
    alpha = float(config.get("alpha", 0.5))

    per_query = []
    recall_scores = {k: [] for k in k_values}
    hit_scores = {k: [] for k in k_values}
    mrr_scores = {k: [] for k in k_values}
    fallback_queries = 0

    for rec in eval_records:
        qid = rec.get("qid")
        gold_evidences = rec.get("evidences", [])
        if not gold_evidences:
            continue

        results = retriever.retrieve(rec.get("query", ""), top_k=k_max, alpha=alpha, mode=mode)
        hits = []
        matched_ids_by_rank: List[Optional[int]] = []
        used_fallback = False

        for chunk in results:
            hit, mode_used, ev_id = match_chunk(chunk, qid, gold_evidences)
            hits.append(hit)
            if hit:
                matched_ids_by_rank.append(ev_id)
                if mode_used == "text":
                    used_fallback = True
            else:
                matched_ids_by_rank.append(None)

        if used_fallback:
            fallback_queries += 1

        total_gold = len(gold_evidences)
        for k in k_values:
            top_hits = hits[:k]
            matched_ids = {ev_id for ev_id in matched_ids_by_rank[:k] if ev_id is not None}
            match_count = len(matched_ids)
            recall_scores[k].append(match_count / total_gold)
            hit_scores[k].append(1.0 if any(top_hits) else 0.0)
            mrr_scores[k].append(reciprocal_rank(top_hits))

        per_query.append(
            {
                "qid": qid,
                "first_hit_rank": (hits.index(True) + 1) if any(hits) else None,
                "matched_evidence_ids": sorted(list({ev_id for ev_id in matched_ids_by_rank if ev_id is not None})),
                "used_fallback": used_fallback,
            }
        )

    metrics = {
        "num_queries": len(per_query),
        "mode": mode,
        "alpha": alpha,
        "uncertain_match_ratio": fallback_queries / len(per_query) if per_query else 0.0,
    }
    for k in k_values:
        metrics[f"recall@{k}"] = mean(recall_scores[k])
        metrics[f"evidence_hit@{k}"] = mean(hit_scores[k])
        metrics[f"mrr@{k}"] = mean(mrr_scores[k])

    metrics_path = os.path.join(run_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    per_query_path = os.path.join(run_dir, "per_query_results.jsonl")
    with open(per_query_path, "w", encoding="utf-8") as f:
        for row in per_query:
            f.write(json.dumps(row) + "\n")

    config_out = os.path.join(run_dir, "config.yaml")
    save_config(config, config_out)

    logger.info("eval_split=%s", eval_split)
    logger.info("corpus_file=%s", corpus_file)
    logger.info("metrics=%s", metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
