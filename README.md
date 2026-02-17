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

## Step4 Multi-step Retrieval

```powershell
# 0) baseline (single-step) eval for comparison
python scripts\eval_retrieval.py --config configs\eval_retrieval.yaml

# 1) build dev subsets
python scripts\build_subsets.py --config configs\build_subsets.yaml

# 2) run multistep + evaluate (full dev)
python scripts\run_multistep_retrieval.py --config configs\run_multistep.yaml
python scripts\eval_multistep_retrieval.py --config configs\eval_multistep.yaml --results outputs/<run_id>/retrieval_results.jsonl

# 3) run multistep on complex subset
python scripts\run_multistep_retrieval.py --config configs\run_multistep.yaml --subset-qids data/subsets/dev_complex_qids.txt
python scripts\eval_multistep_retrieval.py --config configs\eval_multistep.yaml --results outputs/<run_id>/retrieval_results.jsonl --subset-qids data/subsets/dev_complex_qids.txt
```

Outputs:
- `multistep_traces.jsonl`: step-by-step retrieval traces for analysis/case studies.
- `retrieval_results.jsonl`: final chunks per query.
- `metrics.json`, `delta_vs_baseline.json`: evaluation metrics and comparison to baseline.

Notes:
- `top_k_each_step` controls per-step retrieval cost; `top_k_final` controls final output size.
- Ensure `top_k_final >= max(k_values)` for fair Recall@k evaluation (default is 10).

## Step5 Calculator (numeric QA)

```powershell
# 0) build numeric subset
python scripts\build_numeric_subset.py --config configs\build_numeric_subset.yaml

# 1) baseline (single-step) + calculator
python scripts\run_with_calculator.py --config configs\run_with_calculator.yaml
python scripts\eval_numeric.py --config configs\eval_numeric.yaml --predictions outputs/<run_id>/predictions_calc.jsonl

# 2) multistep + calculator (reuse Step4 retrieval results)
python scripts\run_with_calculator.py --config configs\run_with_calculator.yaml --use-multistep 1 --multistep-results outputs/<multistep_run_id>/retrieval_results.jsonl
python scripts\eval_numeric.py --config configs\eval_numeric.yaml --predictions outputs/<run_id>/predictions_calc.jsonl
```

Outputs:
- `facts.jsonl`: extracted numeric facts from evidence.
- `results_R.jsonl`: calculator results per query.
- `calc_traces.jsonl`: calculation traces and rejection reasons.
- `predictions_calc.jsonl`: final answers with fallback info.
- `numeric_metrics.json`: Numeric-EM / error metrics.

## Step6 System Tuning

```powershell
# 0) validate config
python scripts\validate_config.py --config configs\step6_base.yaml

# 1) multistep sweep
python scripts\sweep.py --base-config configs\step6_base.yaml --search-space configs\search_space_multistep.yaml

# 2) calculator threshold sweep
python scripts\sweep.py --base-config configs\step6_base.yaml --search-space configs\search_space_calc.yaml

# 3) run 6-group matrix
python scripts\run_matrix_step6.py --base-config configs\step6_base.yaml --matrix configs\step6_matrix.yaml

# 4) build tables
python scripts\make_tables.py --experiments configs\step6_experiments.yaml
```

## Step7 Paper Draft

```powershell
# 0) ensure tables are up to date
python scripts\make_tables.py --experiments configs\step6_experiments.yaml

# 1) check error analysis summaries
python scripts\error_buckets.py --run-id <run_id>

# optional batch mode (iterate experiments[].run_id)
python scripts\error_buckets.py --config configs\step6_experiments.yaml

# 2) draft chapters are under docs/
# docs/INTRODUCTION.md
# docs/RELATED.md
# docs/METHOD.md
# docs/EXPERIMENT.md
# docs/RESULTS.md
# docs/ERROR_ANALYSIS.md
# docs/DISCUSSION.md
# docs/CONCLUSION.md
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
