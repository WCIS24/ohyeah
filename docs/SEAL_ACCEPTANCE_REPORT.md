# SEAL Acceptance Report

Generated at: 2026-02-17  
Matrix ID: `20260217_123645_68f6b9`  
Seal commit: `27c146e3da3d3b525a7793c90e512103fa649335`

## 1) Run Environment and Preflight

- Smoke passed (`outputs/20260217_123459_5b6847/metrics.json`).
- Smoke log recorded seed + git hash (`outputs/20260217_123459_5b6847/logs.txt:3`).
- Subsets rebuilt:
  - Complex/abbrev stats: `outputs/20260217_123507_c871d6/subsets_stats.json`
  - Numeric stats: `outputs/20260217_123507_1693c0/numeric_subset_stats.json`
- Matrix metadata written:
  - `outputs/20260217_123645_68f6b9/matrix.json`
  - `outputs/20260217_123645_68f6b9/experiments_resolved.yaml`

## 2) MVP10 Core Metrics

| Run label | Run ID (matrix-relative) | Full R@10 | Full MRR@10 | Complex R@10 | Complex MRR@10 | Abbrev R@10 | Abbrev MRR@10 | Numeric EM | Numeric Cov |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| seal_mvp01_preft_dense_singlestep | `20260217_123645_68f6b9_m01` | 0.3246 | 0.2030 | 0.3457 | 0.2330 | 0.3174 | 0.1967 | - | - |
| seal_mvp02_dense_singlestep | `20260217_123645_68f6b9_m02` | 0.3789 | 0.2554 | 0.3951 | 0.2961 | 0.3713 | 0.2497 | - | - |
| seal_mvp03_bm25_singlestep | `20260217_123645_68f6b9_m03` | 0.2246 | 0.1266 | 0.2099 | 0.1266 | 0.2136 | 0.1233 | - | - |
| seal_mvp04_hybrid_singlestep | `20260217_123645_68f6b9_m04` | 0.3491 | 0.2092 | 0.3457 | 0.2159 | 0.3373 | 0.1992 | - | - |
| seal_mvp05_dense_multistep | `20260217_123645_68f6b9_m05` | 0.3789 | 0.2556 | 0.3951 | 0.2965 | 0.3713 | 0.2499 | - | - |
| seal_mvp06_dense_multistep_t1 | `20260217_123645_68f6b9_m06` | 0.3789 | 0.2554 | 0.3951 | 0.2961 | 0.3713 | 0.2497 | - | - |
| seal_mvp07_dense_calc_empty_allow | `20260217_123645_68f6b9_m07` | 0.3789 | 0.2554 | 0.3951 | 0.2961 | 0.3713 | 0.2497 | 0.3964 | 0.6180 |
| seal_mvp08_dense_calc_allow_yoy_diff | `20260217_123645_68f6b9_m08` | 0.3789 | 0.2554 | 0.3951 | 0.2961 | 0.3713 | 0.2497 | 0.3197 | 0.6695 |
| seal_mvp09_dense_multistep_calc | `20260217_123645_68f6b9_m09` | 0.3789 | 0.2556 | 0.3951 | 0.2965 | 0.3713 | 0.2499 | 0.3108 | 0.6760 |
| seal_mvp10_dense_multistep_t1_calc | `20260217_123645_68f6b9_m10` | 0.3789 | 0.2554 | 0.3951 | 0.2961 | 0.3713 | 0.2497 | 0.3108 | 0.6760 |

Source tables:
- `docs/TABLE_MAIN.md`
- `docs/TABLE_NUMERIC.md`

## 3) Multistep Blocked / Stop Summary

| Run | num_queries | avg_steps | stop_reasons | blocked ratio |
| --- | ---: | ---: | --- | ---: |
| `m05_ms` | 570 | 1.081 | `{'MAX_STEPS': 45, 'GATE_BLOCKED': 525}` | 92.11% |
| `m06_ms` | 570 | 1.000 | `{'MAX_STEPS': 46, 'GATE_BLOCKED': 524}` | 91.93% |
| `m09_ms` | 570 | 1.081 | `{'MAX_STEPS': 45, 'GATE_BLOCKED': 525}` | 92.11% |
| `m10_ms` | 570 | 1.000 | `{'MAX_STEPS': 46, 'GATE_BLOCKED': 524}` | 91.93% |

Evidence:
- `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05_ms/logs.txt:7`
- `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05_ms/logs.txt:8`
- `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05_ms/logs.txt:9`
- `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m06_ms/logs.txt:7`
- `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m06_ms/logs.txt:8`
- `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m06_ms/logs.txt:9`
- `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m09_ms/logs.txt:7`
- `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m09_ms/logs.txt:8`
- `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m09_ms/logs.txt:9`
- `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m10_ms/logs.txt:7`
- `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m10_ms/logs.txt:8`
- `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m10_ms/logs.txt:9`

## 4) Calculator Gate / Fallback Summary

| Run | total | ok_ratio | gate_task | gate_task ratio | numeric_em (dev) | coverage (dev) | rel_error_mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `m07_calc` (empty allow list) | 570 | 0.2000 | 570 | 1.0000 | 0.3964 | 0.6180 | 689.2285 |
| `m08_calc` (`["yoy","diff"]`) | 570 | 0.2000 | 465 | 0.8158 | 0.3197 | 0.6695 | 296.5772 |
| `m09_calc` (multistep + calc) | 570 | 0.2053 | 465 | 0.8158 | 0.3108 | 0.6760 | 294.2716 |
| `m10_calc` (T1 multistep + calc) | 570 | 0.2053 | 465 | 0.8158 | 0.3108 | 0.6760 | 294.2716 |

Evidence:
- Gate/fallback counts:
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07_calc/calc_stats.json:17`
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08_calc/calc_stats.json:17`
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m09_calc/calc_stats.json:17`
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m10_calc/calc_stats.json:17`
- Numeric metrics:
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07/summary.json:61`
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m07/summary.json:62`
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/summary.json:61`
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08/summary.json:62`
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m09/summary.json:59`
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m09/summary.json:60`
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m10/summary.json:59`
  - `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m10/summary.json:60`

## 5) Tables and Figures

- Tables generated:
  - `docs/TABLE_MAIN.md`
  - `docs/TABLE_NUMERIC.md`
  - `docs/TABLE_ABLATION.md`
- Plot command completed:
  - run log: `outputs/20260217_140808_4c7530/logs.txt`
  - enabled plot `ablation_breakdown` has data (`has_data=True`).
  - output:
    - `thesis/figures_seal/ThemeA/figures/ablation_breakdown.pdf`
    - `thesis/figures_seal/ThemeA/tables/main_results.csv`
    - `thesis/figures_seal/ThemeA/tables/main_results.tex`

## 6) Seal Checklist

- [x] Smoke passed with logged seed/git hash.
- [x] Subset files rebuilt and stats persisted.
- [x] Matrix run used `run_matrix_step6.py` and produced parent metadata.
- [x] 10/10 matrix experiments finished with `status=ok`.
- [x] Every MVP run has `summary.json`.
- [x] Calculator runs have `calc_stats.json`.
- [x] `make_tables.py` generated full/complex/abbrev/numeric tables.
- [x] `plot_all.py` completed and enabled figure has `has_data=True`.
- [x] Run-level reproducibility artifacts exist (`config.yaml`, resolved config, `git_commit.txt`, logs).

## 7) Binary Decision

**Decision: 可封条（工程执行链路层面）**

Notes (non-blocking):
- This seal matrix uses the current repo’s runnable MVP10 mapping in `configs/step6_matrix_seal.yaml`.
- `plot_all` raised one style warning (`style_not_found`), but figure/table outputs were still generated.
- Calculator `gate_task` remains high (81.58% even after whitelist), so this is a **result-quality risk**, not a pipeline-integrity blocker.
