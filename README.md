# FinDER Financial RAG (Reproducible Skeleton)

Goal: provide a reproducible project scaffold for "baseline -> multi-step retrieval -> calculator -> retriever fine-tuning -> system tuning", plus a runnable smoke test.

## Quick start

Recommended (virtualenv):

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Or via Makefile (if `make` is available):

```powershell
make setup
make smoke
```

## Run smoke test

```powershell
python scripts\smoke.py --config configs\smoke.yaml
```

Outputs are written to `outputs/<run_id>/`:
- `config.yaml`
- `metrics.json`
- `logs.txt`

## Notes

- Default dataset path: `dataset/finder_dataset.csv` (uses a tiny subset for smoke test).
- Retrieval is TF-IDF only; answer generation is a placeholder (no external API).
- If git is not available, commit hash is recorded as `"unknown"`.

## Layout

```
configs/    # YAML configs
scripts/    # CLI scripts
src/        # core library code
data/       # cached data / intermediates (do not commit large files)
outputs/    # experiment outputs
tests/      # unit tests / smoke tests
```
