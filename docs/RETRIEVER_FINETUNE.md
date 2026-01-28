# RETRIEVER FINETUNE

This step fine-tunes a dense retriever on FinDER using supervised contrastive learning.

## Data construction
- Source: `data/processed/train.jsonl`
- Positive chunk: matched by `(qid, evidence_id)` against `data/corpus/chunks.jsonl`.
- Fallback match: normalized text containment if id match missing.
- Hard negatives: mined from BM25 (default) or dense topN; positives are excluded.

Output: `data/processed/train_triplets.jsonl` with fields:
- `qid`, `query`, `pos_chunk_id`, `pos_text`, `hard_negs[{chunk_id,text,score}]`

Stats are written to `outputs/<run_id>/neg_mining_stats.json`.

## Loss
- Default: TripletLoss over (query, pos, hard_neg).
- If hard negatives are disabled: MultipleNegativesRankingLoss (in-batch negatives).

## Training
- Script: `scripts/train_retriever.py`
- Supports: fp16, gradient accumulation, max_steps/num_epochs.
- Evaluates on dev every N steps (subset by `eval_max_queries`/`eval_max_corpus` for speed).
- Best checkpoint saved under `outputs/<run_id>/checkpoints/`.
- Final model saved to `models/retriever_ft/<run_id>` and copied to `models/retriever_ft/latest`.

## Evaluation
- `scripts/eval_retrieval.py` uses the same matching rule as Step2:
  - primary: `(source_qid, evidence_id)` and `doc_id` if present
  - fallback: text containment (records `uncertain_match_ratio`).

## Leakage and splits
- Train on `train.jsonl`, evaluate on `dev.jsonl` only.
- Do not include dev/test queries in mining or training.
