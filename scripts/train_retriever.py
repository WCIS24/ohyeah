from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
from torch.utils.data import DataLoader

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from finder_rag.config import load_config, save_config  # noqa: E402
from finder_rag.logging_utils import setup_logging  # noqa: E402
from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash  # noqa: E402
from retrieval.eval_utils import compute_retrieval_metrics  # noqa: E402
from retrieval.retriever import HybridRetriever  # noqa: E402
from training.pairs import load_jsonl  # noqa: E402


@dataclass
class TrainConfig:
    base_model_name: str
    learning_rate: float
    batch_size: int
    grad_accum: int
    warmup_ratio: float
    weight_decay: float
    num_epochs: int
    max_steps: Optional[int]
    eval_every_steps: int
    save_every_steps: int
    fp16: bool
    bf16: bool
    hard_enabled: bool
    hard_k: int
    temperature: float
    seed: int
    max_train_samples: Optional[int]
    eval_max_queries: Optional[int]
    eval_max_corpus: Optional[int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune retriever")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    return parser.parse_args()


def build_examples(triplets: List[Dict[str, Any]], hard_enabled: bool, hard_k: int):
    from sentence_transformers import InputExample

    examples = []
    missing = 0
    for row in triplets:
        query = row.get("query", "")
        pos = row.get("pos_text", "")
        hard_negs = row.get("hard_negs", [])
        if hard_enabled:
            if not hard_negs:
                missing += 1
                continue
            for neg in hard_negs[:hard_k]:
                examples.append(InputExample(texts=[query, pos, neg.get("text", "")]))
        else:
            examples.append(InputExample(texts=[query, pos]))
    return examples, missing


def evaluate_model(
    model,
    eval_records: List[Dict[str, Any]],
    corpus_chunks: List[Dict[str, Any]],
    k_values: List[int],
    mode: str,
    alpha: float,
    max_queries: Optional[int] = None,
    max_corpus: Optional[int] = None,
):
    if max_queries:
        eval_records = eval_records[:max_queries]
    if max_corpus:
        corpus_chunks = corpus_chunks[:max_corpus]

    retriever = HybridRetriever(
        model_name=model,  # SentenceTransformer instance supported
        use_faiss=False,
        device=None,
        batch_size=32,
    )
    retriever.build_index(corpus_chunks)
    metrics, _ = compute_retrieval_metrics(
        eval_records=eval_records,
        retriever=retriever,
        k_values=k_values,
        mode=mode,
        alpha=alpha,
    )
    return metrics


class RetrievalEvaluator:
    def __init__(
        self,
        eval_records: List[Dict[str, Any]],
        corpus_chunks: List[Dict[str, Any]],
        k_values: List[int],
        mode: str,
        alpha: float,
        max_queries: Optional[int],
        max_corpus: Optional[int],
        run_dir: str,
        logger,
    ) -> None:
        self.eval_records = eval_records
        self.corpus_chunks = corpus_chunks
        self.k_values = k_values
        self.mode = mode
        self.alpha = alpha
        self.max_queries = max_queries
        self.max_corpus = max_corpus
        self.run_dir = run_dir
        self.logger = logger
        self.best_score = -1.0

    def __call__(self, model, output_path=None, epoch=-1, steps=-1):
        metrics = evaluate_model(
            model,
            self.eval_records,
            self.corpus_chunks,
            self.k_values,
            self.mode,
            self.alpha,
            self.max_queries,
            self.max_corpus,
        )
        score = metrics.get("recall@5", 0.0)
        tag = f"epoch{epoch}_steps{steps}"
        metrics_path = os.path.join(self.run_dir, f"eval_{tag}.json")
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        self.logger.info("eval_%s=%s", tag, metrics)
        if score > self.best_score:
            self.best_score = score
        return score


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

    train_cfg = TrainConfig(
        base_model_name=config.get("base_model_name", "sentence-transformers/all-MiniLM-L6-v2"),
        learning_rate=float(config.get("learning_rate", 2e-5)),
        batch_size=int(config.get("batch_size", 16)),
        grad_accum=int(config.get("grad_accum", 1)),
        warmup_ratio=float(config.get("warmup_ratio", 0.1)),
        weight_decay=float(config.get("weight_decay", 0.0)),
        num_epochs=int(config.get("num_epochs", 1)),
        max_steps=config.get("max_steps"),
        eval_every_steps=int(config.get("eval_every_steps", 500)),
        save_every_steps=int(config.get("save_every_steps", 500)),
        fp16=bool(config.get("fp16", False)),
        bf16=bool(config.get("bf16", False)),
        hard_enabled=bool(config.get("hard_negatives", {}).get("enabled", True)),
        hard_k=int(config.get("hard_negatives", {}).get("hard_k", 1)),
        temperature=float(config.get("hard_negatives", {}).get("temperature", 0.05)),
        seed=seed,
        max_train_samples=config.get("max_train_samples"),
        eval_max_queries=config.get("eval_max_queries"),
        eval_max_corpus=config.get("eval_max_corpus"),
    )

    triplets_path = config.get("train_triplets_path", "data/processed/train_triplets.jsonl")
    triplets = load_jsonl(triplets_path)
    if train_cfg.max_train_samples:
        triplets = triplets[: int(train_cfg.max_train_samples)]

    examples, missing = build_examples(triplets, train_cfg.hard_enabled, train_cfg.hard_k)
    missing_ratio = missing / len(triplets) if triplets else 0.0
    logger.info("train_examples=%d missing_hard_neg_ratio=%.4f", len(examples), missing_ratio)

    from sentence_transformers import SentenceTransformer, losses

    model = SentenceTransformer(train_cfg.base_model_name)

    if train_cfg.hard_enabled:
        train_loss = losses.TripletLoss(model=model)
    else:
        train_loss = losses.MultipleNegativesRankingLoss(model=model)

    train_dataloader = DataLoader(
        examples,
        batch_size=train_cfg.batch_size,
        shuffle=True,
        collate_fn=model.smart_batching_collate,
    )

    eval_split_path = config.get("eval_split_path", "data/processed/dev.jsonl")
    corpus_path = config.get("corpus_path", "data/corpus/chunks.jsonl")
    eval_records = load_jsonl(eval_split_path)
    corpus_chunks = load_jsonl(corpus_path)

    k_values = [int(k) for k in config.get("k_values", [1, 5, 10])]
    eval_mode = config.get("eval_mode", "dense")
    eval_alpha = float(config.get("eval_alpha", 0.5))

    evaluator = RetrievalEvaluator(
        eval_records=eval_records,
        corpus_chunks=corpus_chunks,
        k_values=k_values,
        mode=eval_mode,
        alpha=eval_alpha,
        max_queries=train_cfg.eval_max_queries,
        max_corpus=train_cfg.eval_max_corpus,
        run_dir=run_dir,
        logger=logger,
    )

    checkpoints_dir = os.path.join(run_dir, "checkpoints")
    ensure_dir(checkpoints_dir)

    total_steps = len(train_dataloader) * train_cfg.num_epochs
    if train_cfg.max_steps is not None:
        total_steps = min(total_steps, int(train_cfg.max_steps))

    warmup_steps = int(total_steps * train_cfg.warmup_ratio)
    logger.info(
        "train_cfg=%s warmup_steps=%d eval_every=%d save_every=%d total_steps=%d",
        train_cfg,
        warmup_steps,
        train_cfg.eval_every_steps,
        train_cfg.save_every_steps,
        total_steps,
    )

    import torch
    from transformers import get_linear_schedule_with_warmup

    optimizer = torch.optim.AdamW(
        model.parameters(), lr=train_cfg.learning_rate, weight_decay=train_cfg.weight_decay
    )
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
    )

    scaler = torch.cuda.amp.GradScaler(enabled=train_cfg.fp16 and torch.cuda.is_available())
    model.train()

    global_step = 0
    best_score = -1.0

    for epoch in range(train_cfg.num_epochs):
        for batch in train_dataloader:
            features, labels = batch
            if train_cfg.fp16 and torch.cuda.is_available():
                with torch.cuda.amp.autocast():
                    loss_value = train_loss(features, labels)
                scaler.scale(loss_value).backward()
            else:
                loss_value = train_loss(features, labels)
                loss_value.backward()

            if (global_step + 1) % train_cfg.grad_accum == 0:
                if train_cfg.fp16 and torch.cuda.is_available():
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    optimizer.step()
                scheduler.step()
                optimizer.zero_grad()

            global_step += 1

            if train_cfg.eval_every_steps and global_step % train_cfg.eval_every_steps == 0:
                score = evaluator(model, epoch=epoch, steps=global_step)
                if score > best_score:
                    best_score = score
                    best_path = os.path.join(checkpoints_dir, "best_model")
                    model.save(best_path)

            if train_cfg.save_every_steps and global_step % train_cfg.save_every_steps == 0:
                checkpoint_path = os.path.join(checkpoints_dir, f"step_{global_step}")
                model.save(checkpoint_path)

            if train_cfg.max_steps is not None and global_step >= int(train_cfg.max_steps):
                break
        if train_cfg.max_steps is not None and global_step >= int(train_cfg.max_steps):
            break

    model_dir = os.path.join("models", "retriever_ft", run_id)
    ensure_dir(model_dir)
    model.save(model_dir)

    latest_dir = os.path.join("models", "retriever_ft", "latest")
    if os.path.exists(latest_dir):
        shutil.rmtree(latest_dir)
    shutil.copytree(model_dir, latest_dir)

    config_out = os.path.join(run_dir, "train_config.yaml")
    save_config(config, config_out)

    metrics = {
        "best_recall@5": best_score,
        "total_steps": global_step,
        "num_epochs": train_cfg.num_epochs,
        "max_steps": train_cfg.max_steps,
        "hard_negatives_enabled": train_cfg.hard_enabled,
        "hard_k": train_cfg.hard_k,
        "missing_hard_neg_ratio": missing_ratio,
        "eval_every_steps": train_cfg.eval_every_steps,
    }
    metrics_path = os.path.join(run_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    logger.info("model_dir=%s", model_dir)
    logger.info("checkpoints_dir=%s", checkpoints_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
