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
