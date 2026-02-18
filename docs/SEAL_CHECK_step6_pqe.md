# SEAL Check - Step6 PQE (Module X)

Date: 2026-02-18
Branch: `feat/pqe_replace_multistep`

## 0) Verdict

Verdict: `PARTIAL PASS`.

- PQE is integrated, triggerable, and auditable (`qexpand_stats.json` is produced when enabled).
- Retrieval metrics improved versus dense single-step baseline.
- Current uplift does not yet meet the proposed `+0.010` abbrev threshold.

## 1) Reproducible commands

```bash
python scripts/smoke.py --config configs/smoke.yaml --run-id pqe_smoke_pre
python scripts/validate_config.py --config configs/step6_base.yaml
python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix configs/tmp_matrix_pqe.yaml
```

Additional ablations run with `scripts/run_experiment.py`:

- `20260218_092521_637290_m03` (PQE abbrev-only; PRF-year off)
- `20260218_092521_637290_m05` (PQE + calculator)

## 2) Run artefacts

Matrix root:
- `outputs/20260218_092521_637290/`

Key summaries:
- Baseline off: `outputs/20260218_092521_637290/runs/20260218_092521_637290_m01/summary.json`
- PQE on: `outputs/20260218_092521_637290/runs/20260218_092521_637290_m02/summary.json`
- PQE abbrev-only: `outputs/20260218_092521_637290/runs/20260218_092521_637290_m03/summary.json`
- PQE + calculator: `outputs/20260218_092521_637290/runs/20260218_092521_637290_m05/summary.json`

PQE traces:
- `outputs/20260218_092521_637290/runs/20260218_092521_637290_m02_retrieval_full/qexpand_stats.json`
- `outputs/20260218_092521_637290/runs/20260218_092521_637290_m03_retrieval_full/qexpand_stats.json`

## 3) Retrieval deltas vs baseline (`m01`)

`m02` (PQE on):
- `full_r10`: `+0.0053`
- `full_mrr10`: `+0.0029`
- `complex_r10`: `+0.0123`
- `complex_mrr10`: `+0.0040`
- `abbrev_r10`: `+0.0040`
- `abbrev_mrr10`: `+0.0030`

`m03` (abbrev-only):
- Near-zero change on all retrieval slices.

Interpretation:
- Measurable gains are driven by PRF-year expansion, not acronym-only expansion under current settings.

## 4) PQE trigger evidence

From `m02` full retrieval:
- `queries_expanded`: `483 / 570`
- `abbrev_expanded_count`: `11`
- `prf_year_expanded_count`: `483`

From `m03` full retrieval (abbrev-only):
- `queries_expanded`: `11 / 570`
- `abbrev_expanded_count`: `11`
- `prf_year_expanded_count`: `0`

## 5) Numeric interaction check

Compared against existing calc baseline `seal_mvp08_dense_calc_allow_yoy_diff`
(`outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/summary.json`):

- `num_em`: `0.3197 -> 0.3079` (`-0.0118`)
- `num_cov`: `0.6695 -> 0.6867` (`+0.0172`)

Interpretation:
- Retrieval quality improved, coverage rose, but numeric EM declined slightly.
- This is consistent with the prior hypothesis that calculator correctness is now the limiting factor.

## 6) Next action

- Keep `m11/m12/m13` appended in `configs/step6_matrix_seal.yaml`.
- Run full seal matrix and then register new run IDs in `configs/step6_experiments_seal.yaml`.
