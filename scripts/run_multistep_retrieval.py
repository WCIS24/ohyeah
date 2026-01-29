from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import Counter
from typing import Any, Dict, List, Optional

import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402
from multistep.engine import MultiStepConfig, MultiStepRetriever  # noqa: E402
from training.pairs import load_jsonl  # noqa: E402
from retrieval.retriever import HybridRetriever  # noqa: E402
from config.schema import (  # noqa: E402
    get_path,
    resolve_config,
    validate_config,
    validate_paths,
    write_resolved_config,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run rule-based multi-step retrieval")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--subset-qids", default=None, help="Optional subset qid list path")
    parser.add_argument("--max-steps", type=int, default=None, help="Override max steps")
    parser.add_argument("--novelty-threshold", type=float, default=None)
    parser.add_argument("--gap-enabled", type=int, default=None, help="1/0")
    parser.add_argument("--refiner-enabled", type=int, default=None, help="1/0")
    return parser.parse_args()


def apply_overrides(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    if args.subset_qids is not None:
        config["subset_qids_path"] = args.subset_qids
    if args.max_steps is not None:
        config["max_steps"] = args.max_steps
    if args.novelty_threshold is not None:
        config["novelty_threshold"] = args.novelty_threshold
    if args.gap_enabled is not None:
        config["gap_enabled"] = bool(args.gap_enabled)
    if args.refiner_enabled is not None:
        config["refiner_enabled"] = bool(args.refiner_enabled)
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

    resolved = resolve_config(raw_config)
    resolved_path = write_resolved_config(resolved, run_dir)
    issues = validate_config(resolved) + validate_paths(resolved)
    logger.info("resolved_config_path=%s", resolved_path)
    if issues:
        logger.info("config_issues=%s", issues)

    seed = int(get_path(resolved, "runtime.seed", 42))
    random.seed(seed)
    np.random.seed(seed)
    git_hash = get_git_hash()
    raw_config["git_hash"] = git_hash
    logger.info("seed=%d git_hash=%s", seed, git_hash)

    processed_dir = get_path(resolved, "data.processed_dir", "data/processed")
    eval_file = get_path(resolved, "data.splits.dev", "dev.jsonl")
    dev_path = os.path.join(processed_dir, eval_file)
    corpus_dir = get_path(resolved, "data.corpus_dir", "data/corpus")
    corpus_file = get_path(resolved, "data.corpus_file", "chunks.jsonl")
    corpus_path = os.path.join(corpus_dir, corpus_file)

    records = load_jsonl(dev_path)
    subset_qids = load_subset(raw_config.get("subset_qids_path"))
    if subset_qids:
        records = [r for r in records if r.get("qid") in subset_qids]

    corpus_chunks = load_jsonl(corpus_path)

    retriever_cfg = resolved.get("retriever", {})
    retriever = HybridRetriever(
        model_name=get_path(resolved, "retriever.dense.model_name_or_path"),
        use_faiss=bool(get_path(resolved, "retriever.index.use_faiss", False)),
        device=retriever_cfg.get("device"),
        batch_size=int(retriever_cfg.get("batch_size", 32)),
    )
    retriever.build_index(corpus_chunks)
    logger.info("dense_model_loaded=%s", retriever.loaded_model_name)

    ms_config = MultiStepConfig(
        max_steps=int(get_path(resolved, "multistep.max_steps", 3)),
        top_k_each_step=int(get_path(resolved, "multistep.top_k_each_step", 5)),
        final_top_k=int(get_path(resolved, "retriever.top_k", 5)),
        alpha=float(get_path(resolved, "retriever.hybrid.alpha", 0.5)),
        mode=get_path(resolved, "retriever.mode", "dense"),
        novelty_threshold=float(get_path(resolved, "multistep.novelty_threshold", 0.3)),
        stop_no_new_steps=int(get_path(resolved, "multistep.stop_no_new_steps", 2)),
        merge_strategy=str(get_path(resolved, "multistep.merge_strategy", "maxscore")),
        gate_enabled=bool(get_path(resolved, "multistep.gate.enabled", True)),
        gate_min_gap_conf=float(get_path(resolved, "multistep.gate.min_gap_conf", 0.3)),
        gate_allow_types=list(
            get_path(resolved, "multistep.gate.allow_types", ["YEAR", "COMPARE"])
        ),
        gap_enabled=bool(get_path(resolved, "multistep.gate.enabled", True)),
        refiner_enabled=bool(raw_config.get("refiner_enabled", True)),
    )

    chunk_size = int(get_path(resolved, "chunking.chunk_size", 0))
    overlap = int(get_path(resolved, "chunking.overlap", 0))
    logger.info(
        "dense_model=%s mode=%s alpha=%.3f chunk_size=%d overlap=%d merge=%s gate_min=%.2f",
        retriever.loaded_model_name,
        ms_config.mode,
        ms_config.alpha,
        chunk_size,
        overlap,
        ms_config.merge_strategy,
        ms_config.gate_min_gap_conf,
    )

    engine = MultiStepRetriever(retriever, ms_config)

    traces_path = os.path.join(run_dir, "multistep_traces.jsonl")
    results_path = os.path.join(run_dir, "retrieval_results.jsonl")

    stop_counts = Counter()
    total_steps = 0
    total_new = 0
    total_topk = 0

    with open(traces_path, "w", encoding="utf-8") as traces_f, open(
        results_path, "w", encoding="utf-8"
    ) as results_f:
        for rec in records:
            qid = rec.get("qid")
            query = rec.get("query", "")
            collected, trace, stop_reason, final_top = engine.run(query)

            stop_counts[stop_reason] += 1
            total_steps += len(trace)
            total_new += sum(len(t["newly_added_chunk_ids"]) for t in trace)
            total_topk += sum(len(t["topk_chunks"]) for t in trace)

            traces_f.write(json.dumps({"qid": qid, "trace": trace}) + "\n")

            collected_chunks = [
                {
                    "chunk_id": c.get("chunk_id"),
                    "score": c.get("score"),
                    "meta": c.get("meta"),
                    "text": c.get("text"),
                }
                for c in collected
            ]

            results_f.write(
                json.dumps(
                    {
                        "qid": qid,
                        "final_top_chunks": final_top,
                        "all_collected_chunks": collected_chunks,
                        "stop_reason": stop_reason,
                        "steps_used": len(trace),
                    }
                )
                + "\n"
            )

    avg_steps = total_steps / len(records) if records else 0.0
    avg_new_per_step = total_new / total_steps if total_steps else 0.0
    avg_topk_per_step = total_topk / total_steps if total_steps else 0.0

    logger.info("num_queries=%d", len(records))
    logger.info(
        "avg_steps=%.3f avg_new_per_step=%.3f avg_topk_per_step=%.3f",
        avg_steps,
        avg_new_per_step,
        avg_topk_per_step,
    )
    logger.info("stop_reasons=%s", dict(stop_counts))

    with open(os.path.join(run_dir, "git_commit.txt"), "w", encoding="utf-8") as f:
        f.write(f"{git_hash}\n")

    config_out = os.path.join(run_dir, "config.yaml")
    save_config(resolved, config_out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
