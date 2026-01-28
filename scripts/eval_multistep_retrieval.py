from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402
from retrieval.eval_utils import match_chunk  # noqa: E402
from training.pairs import load_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate multistep retrieval")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--results", default=None, help="Override retrieval_results.jsonl")
    parser.add_argument("--subset-qids", default=None, help="Override subset qids path")
    return parser.parse_args()


def apply_overrides(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    if args.results is not None:
        config["results_path"] = args.results
    if args.subset_qids is not None:
        config["subset_qids_path"] = args.subset_qids
    return config


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def reciprocal_rank(hits: List[bool]) -> float:
    for idx, hit in enumerate(hits, start=1):
        if hit:
            return 1.0 / idx
    return 0.0


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

    dev_path = config.get("processed_dev_path", "data/processed/dev.jsonl")
    results_path = config.get("results_path")
    if not results_path or not os.path.exists(results_path):
        logger.error("missing results_path: %s", results_path)
        return 2

    records = load_jsonl(dev_path)
    results = {r["qid"]: r for r in load_jsonl(results_path)}

    subset_qids = load_subset(config.get("subset_qids_path"))
    if subset_qids:
        records = [r for r in records if r.get("qid") in subset_qids]

    k_values = [int(k) for k in config.get("k_values", [1, 5, 10])]
    use_collected = bool(config.get("use_collected", False))

    recall_scores = {k: [] for k in k_values}
    hit_scores = {k: [] for k in k_values}
    mrr_scores = {k: [] for k in k_values}
    fallback_queries = 0
    per_query = []

    for rec in records:
        qid = rec.get("qid")
        gold_evidences = rec.get("evidences", [])
        if not gold_evidences:
            continue
        res = results.get(qid)
        if not res:
            continue

        if use_collected:
            retrieved = res.get("all_collected_chunks", [])
        else:
            retrieved = res.get("final_top_chunks", [])

        retrieved = sorted(retrieved, key=lambda x: x.get("score", 0.0), reverse=True)
        hits = []
        matched_ids_by_rank = []
        used_fallback = False

        for r in retrieved:
            meta = r.get("meta") or {"chunk_id": r.get("chunk_id")}
            chunk = {"meta": meta, "text": r.get("text", "")}
            hit, mode_used, ev_id = match_chunk(chunk, qid, gold_evidences)
            hits.append(hit)
            matched_ids_by_rank.append(ev_id if hit else None)
            if hit and mode_used == "text":
                used_fallback = True

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
                "used_fallback": used_fallback,
            }
        )

    metrics = {
        "num_queries": len(per_query),
        "use_collected": use_collected,
        "uncertain_match_ratio": fallback_queries / len(per_query) if per_query else 0.0,
    }
    for k in k_values:
        metrics[f"recall@{k}"] = mean(recall_scores[k])
        metrics[f"evidence_hit@{k}"] = mean(hit_scores[k])
        metrics[f"mrr@{k}"] = mean(mrr_scores[k])

    metrics_path = os.path.join(run_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    per_query_path = os.path.join(run_dir, "per_query.jsonl")
    with open(per_query_path, "w", encoding="utf-8") as f:
        for row in per_query:
            f.write(json.dumps(row) + "\n")

    baseline_metrics_path = config.get("baseline_metrics_path")
    if baseline_metrics_path and os.path.exists(baseline_metrics_path):
        with open(baseline_metrics_path, "r", encoding="utf-8") as f:
            base = json.load(f)
        delta = {}
        for key, val in metrics.items():
            if key in base and isinstance(val, (int, float)):
                delta[key] = val - base[key]
        delta_path = os.path.join(run_dir, "delta_vs_baseline.json")
        with open(delta_path, "w", encoding="utf-8") as f:
            json.dump({"delta": delta, "baseline": base, "multistep": metrics}, f, indent=2)

    config_out = os.path.join(run_dir, "config.yaml")
    save_config(config, config_out)

    logger.info("metrics=%s", metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
