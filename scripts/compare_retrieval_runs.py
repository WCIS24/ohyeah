from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from finder_rag.config import load_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir  # noqa: E402
from retrieval.retriever import HybridRetriever  # noqa: E402
from training.pairs import load_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare pre/post retrieval runs")
    parser.add_argument("--pre-run", required=True, help="outputs/<run_id> for pre_ft")
    parser.add_argument("--post-run", required=True, help="outputs/<run_id> for post_ft")
    parser.add_argument("--eval-config", required=True, help="eval_retrieval config used")
    return parser.parse_args()


def load_metrics(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_per_query(path: str) -> Dict[str, Dict[str, Any]]:
    rows = load_jsonl(path)
    return {row["qid"]: row for row in rows if row.get("qid")}


def rank_value(rank) -> int:
    return rank if rank is not None else 999


def select_top_changes(pre: Dict[str, Any], post: Dict[str, Any], top_n: int = 20):
    deltas = []
    for qid, pre_row in pre.items():
        post_row = post.get(qid)
        if not post_row:
            continue
        pre_rank = rank_value(pre_row.get("first_hit_rank"))
        post_rank = rank_value(post_row.get("first_hit_rank"))
        delta = pre_rank - post_rank
        deltas.append((qid, delta, pre_rank, post_rank))
    deltas_sorted = sorted(deltas, key=lambda x: x[1], reverse=True)
    improved = deltas_sorted[:top_n]
    declined = deltas_sorted[-top_n:][::-1]
    return improved, declined


def load_model_name(run_dir: str) -> str:
    config_path = os.path.join(run_dir, "config.yaml")
    if os.path.exists(config_path):
        config = load_config(config_path)
        retriever_cfg = config.get("retriever", {})
        model_name = retriever_cfg.get("model_name")
        if model_name:
            return model_name
    raise FileNotFoundError(f"model_name not found in {run_dir}/config.yaml")


def main() -> int:
    args = parse_args()
    pre_dir = args.pre_run
    post_dir = args.post_run
    eval_cfg = load_config(args.eval_config)

    log_path = os.path.join(post_dir, "logs.txt")
    logger = setup_logging(log_path)
    logger.info("compare pre=%s post=%s", pre_dir, post_dir)

    pre_metrics = load_metrics(os.path.join(pre_dir, "metrics.json"))
    post_metrics = load_metrics(os.path.join(post_dir, "metrics.json"))

    delta = {}
    for key in ["recall@5", "recall@10", "mrr@10", "mrr@5", "recall@1", "mrr@1"]:
        if key in pre_metrics and key in post_metrics:
            delta[key] = post_metrics[key] - pre_metrics[key]

    delta_path = os.path.join(post_dir, "delta_vs_pre.json")
    with open(delta_path, "w", encoding="utf-8") as f:
        json.dump({"delta": delta, "pre": pre_metrics, "post": post_metrics}, f, indent=2)

    pre_per_query = load_per_query(os.path.join(pre_dir, "per_query_results.jsonl"))
    post_per_query = load_per_query(os.path.join(post_dir, "per_query_results.jsonl"))
    improved, declined = select_top_changes(pre_per_query, post_per_query, top_n=20)

    eval_split_path = eval_cfg.get("processed_dir", "data/processed")
    eval_split = eval_cfg.get("eval_split", "dev")
    eval_path = os.path.join(eval_split_path, f"{eval_split}.jsonl")
    eval_records = {row["qid"]: row for row in load_jsonl(eval_path)}

    corpus_path = eval_cfg.get("corpus_file", "data/corpus/chunks.jsonl")
    corpus_chunks = load_jsonl(corpus_path)

    pre_model = load_model_name(pre_dir)
    post_model = load_model_name(post_dir)

    retriever_pre = HybridRetriever(
        model_name=pre_model,
        use_faiss=bool(eval_cfg.get("retriever", {}).get("use_faiss", False)),
        device=eval_cfg.get("retriever", {}).get("device"),
        batch_size=int(eval_cfg.get("retriever", {}).get("batch_size", 32)),
    )
    retriever_post = HybridRetriever(
        model_name=post_model,
        use_faiss=bool(eval_cfg.get("retriever", {}).get("use_faiss", False)),
        device=eval_cfg.get("retriever", {}).get("device"),
        batch_size=int(eval_cfg.get("retriever", {}).get("batch_size", 32)),
    )
    retriever_pre.build_index(corpus_chunks)
    retriever_post.build_index(corpus_chunks)

    top_k = max([int(k) for k in eval_cfg.get("k_values", [1, 5, 10])])
    mode = eval_cfg.get("mode", "dense")
    alpha = float(eval_cfg.get("alpha", 0.5))

    def collect(qids):
        rows = []
        for qid, delta_val, pre_rank, post_rank in qids:
            record = eval_records.get(qid)
            if not record:
                continue
            query = record.get("query", "")
            pre_results = retriever_pre.retrieve(query, top_k=top_k, mode=mode, alpha=alpha)
            post_results = retriever_post.retrieve(query, top_k=top_k, mode=mode, alpha=alpha)
            rows.append(
                {
                    "qid": qid,
                    "delta_rank": delta_val,
                    "pre_rank": pre_rank,
                    "post_rank": post_rank,
                    "query": query,
                    "pre_topk": [
                        {
                            "chunk_id": r.get("meta", {}).get("chunk_id"),
                            "score": r.get("score"),
                        }
                        for r in pre_results
                    ],
                    "post_topk": [
                        {
                            "chunk_id": r.get("meta", {}).get("chunk_id"),
                            "score": r.get("score"),
                        }
                        for r in post_results
                    ],
                }
            )
        return rows

    analysis_rows = []
    analysis_rows.extend(collect(improved))
    analysis_rows.extend(collect(declined))

    analysis_path = os.path.join(post_dir, "error_analysis_top20.jsonl")
    with open(analysis_path, "w", encoding="utf-8") as f:
        for row in analysis_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    logger.info("delta_path=%s", delta_path)
    logger.info("analysis_path=%s", analysis_path)
    logger.info("delta=%s", delta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
