# FinDER Financial RAG (Reproducible Skeleton)

Goal: reproducible project scaffold for "baseline -> multi-step retrieval -> calculator -> retriever fine-tuning -> system tuning", plus a runnable smoke test and baseline pipeline.

## Setup

Recommended (virtualenv):

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

If `make` is available:

```powershell
make setup
```

## Smoke test

```powershell
python scripts\smoke.py --config configs\smoke.yaml
```

Outputs are written to `outputs/<run_id>/`:
- `config.yaml`
- `metrics.json`
- `logs.txt`

If `dataset/finder_dataset.csv` is missing, the smoke script auto-downloads a tiny subset
from `Linq-AI-Research/FinDER` (HF) and caches it under `data/finder_subset.csv`.

Metrics field mapping:
- `recall@5`: Recall@5 for retrieval (smoke k defaults to 5).
- `em`: exact match for placeholder QA.
- For compatibility, `recall_at_k` and `exact_match` are also included.

## Full pipeline (baseline)

1) Prepare data (schema inspection + normalization + splits):

```powershell
python scripts\prepare_data.py --config configs\prepare_data.yaml
```

2) Build corpus chunks:

```powershell
python scripts\build_corpus.py --config configs\build_corpus.yaml
```

3) Retrieval evaluation:

```powershell
python scripts\eval_retrieval.py --config configs\eval_retrieval.yaml
```

4) Run baseline RAG (single-step retrieval):

```powershell
python scripts\run_baseline.py --config configs\run_baseline.yaml
```

5) Evaluate QA:

```powershell
python scripts\eval_qa.py --config configs\eval_qa.yaml --predictions outputs/<run_id>/predictions.jsonl --gold data/processed/dev.jsonl
```

## Step3 Retriever Fine-tune

```powershell
# 0) (once) prepare data + corpus
python scripts\prepare_data.py --config configs\prepare_data.yaml
python scripts\build_corpus.py --config configs\build_corpus.yaml

# 1) mine hard negatives
python scripts\mine_hard_negatives.py --config configs\mine_hard_negatives.yaml

# 2) train retriever
python scripts\train_retriever.py --config configs\train_retriever.yaml

# 3) pre/post evaluation
python scripts\eval_retrieval.py --config configs\eval_retrieval.yaml

# 4) compare runs (fill in pre/post run_id)
python scripts\compare_retrieval_runs.py --pre-run outputs/<pre_run_id> --post-run outputs/<post_run_id> --eval-config configs/eval_retrieval.yaml
```

## FAISS note

- The retriever tries to use FAISS for dense indexing when available.
- If FAISS is not installed or unsupported, it falls back to NumPy brute-force.
- Optional install: `pip install faiss-cpu` (platform support varies).

## Layout

```
configs/    # YAML configs
scripts/    # CLI scripts
src/        # core library code
  data/     # dataset loading/normalization
  indexing/ # chunking
  retrieval/# retrievers
  finder_rag/ # shared utilities
outputs/    # experiment outputs
```
