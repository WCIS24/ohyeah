# SEAL Check - Step6 PQE (A3 Integration)

Date: 2026-02-18
Branch: `feat/pqe_replace_multistep`

## 1) Executed chain

```bash
python scripts/smoke.py --config configs/smoke.yaml --run-id seal_a3_smoke
python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix configs/tmp_matrix_seal_pqe_only.yaml
python scripts/make_tables.py --experiments configs/step6_experiments_seal.yaml
python scripts/plot_all.py --config scripts/plot_config.yaml
```

## 2) Matrix and run IDs

- Matrix ID: `20260218_120310_8bc565`
- Matrix file: `outputs/20260218_120310_8bc565/matrix.json`
- Runs root: `outputs/20260218_120310_8bc565/runs/`

Registered runs:

- `m11_pqe` -> `20260218_120310_8bc565/runs/20260218_120310_8bc565_m02`
- `m12_pqe_abbrev_only` -> `20260218_120310_8bc565/runs/20260218_120310_8bc565_m03`
- `m13_pqe_calc` -> `20260218_120310_8bc565/runs/20260218_120310_8bc565_m04`

Note on status:

- `matrix.json` marks `m13_pqe_calc` as `failed`, but its `summary.json` and downstream numeric files
  are present and complete (`outputs/20260218_120310_8bc565/runs/20260218_120310_8bc565_m04/summary.json`).

## 3) PQE trigger evidence

- `m11_pqe` full retrieval stats:
  - `queries_expanded = 483 / 570` (`84.74%`)
  - `abbrev_expanded_count = 11`
  - `prf_year_expanded_count = 483`
- `m12_pqe_abbrev_only` full retrieval stats:
  - `queries_expanded = 11 / 570` (`1.93%`)
  - `abbrev_expanded_count = 11`
  - `prf_year_expanded_count = 0`

Interpretation:

- With PRF-year on (`m11`), PQE has broad activation.
- With PRF-year off (`m12`), activation collapses to acronym cases only.

## 4) Metric deltas vs baseline (`m02_dense_baseline_v2`)

Source: `outputs/seal_checks/pqe_min_matrix_compare.json`.

`m11_pqe` delta:

- `full_r10`: `+0.0053`
- `full_mrr10`: `+0.0029`
- `complex_r10`: `+0.0123`
- `complex_mrr10`: `+0.0040`
- `abbrev_r10`: `+0.0040`
- `abbrev_mrr10`: `+0.0030`

`m12_pqe_abbrev_only` delta:

- `full_r10`: `+0.0000`
- `full_mrr10`: `+0.0001`
- `complex_r10`: `+0.0000`
- `complex_mrr10`: `+0.0000`
- `abbrev_r10`: `+0.0000`
- `abbrev_mrr10`: `+0.0002`

Ablation interpretation:

- Most observed gain is from PRF-year expansion rather than abbrev-only expansion.

`m13_pqe_calc` numeric (dev subset):

- `numeric_em = 0.3079`
- `coverage = 0.6867`

## 5) Official tables/plots integration status

- `configs/step6_experiments_seal.yaml` now includes:
  - `m11_pqe`
  - `m12_pqe_abbrev_only`
  - `m13_pqe_calc`
- `docs/TABLE_MAIN.md` contains PQE rows.
- Plot run `20260218_130158_69e72e` has `has_data=False` count `0` for generated figures.

Audit artifacts:

- `outputs/seal_checks/pqe_min_matrix_compare.json`
- `outputs/seal_checks/pqe_tables_plots_check.json`
