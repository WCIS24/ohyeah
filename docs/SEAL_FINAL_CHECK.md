# SEAL Final Check

Generated at: 2026-02-28 18:33:41 Asia/Shanghai
Decision: READY
Machine-readable snapshot: `outputs/seal_checks/seal_final_snapshot.json`

## 1. Seal Summary

| Item | Value |
| --- | --- |
| smoke_run_id | `seal_final_smoke` |
| matrix_id | `20260228_055920_06d6bb` |
| plot_run_id | `20260228_103340_cb1bb1` |
| commit_now | `427933035d8144eca44ac919fd0a9c2692469f6e` |
| matrix_status | `20/20 ok` |
| plot_has_data_false_count | `0` |
| tables_updated | `Yes` |
| plots_updated | `Yes` |

## 2. Acceptance Items

| Check item | Result | Evidence path |
| --- | --- | --- |
| Smoke ran before experiments and passed | Pass | `outputs/seal_final_smoke/metrics.json`, `outputs/seal_final_smoke/logs.txt`, `outputs/seal_final_smoke/env_versions.json` |
| Seal matrix metadata exists | Pass | `outputs/20260228_055920_06d6bb/matrix.json`, `outputs/20260228_055920_06d6bb/experiments_resolved.yaml` |
| All 20 seal runs reached `status=ok` | Pass | `outputs/20260228_055920_06d6bb/matrix.json`, `outputs/seal_checks/seal_final_snapshot.json` |
| Seal experiments mapping points to this matrix | Pass | `configs/step6_experiments_seal.yaml`, `outputs/seal_checks/seal_final_snapshot.json` |
| Main / numeric / ablation tables were regenerated from the seal experiments list | Pass | `docs/TABLE_MAIN.md`, `docs/TABLE_NUMERIC.md`, `docs/TABLE_ABLATION.md` |
| Plot outputs were regenerated from the seal plot config | Pass | `outputs/20260228_103340_cb1bb1/logs.txt`, `thesis/figures_seal/ThemeA/figures/ablation_breakdown.pdf`, `thesis/figures_seal/ThemeA/tables/main_results.csv` |
| Enabled plots have `has_data=False` count = 0 | Pass | `outputs/20260228_103340_cb1bb1/logs.txt`, `outputs/seal_checks/seal_final_snapshot.json` |
| Machine-readable seal snapshot was written | Pass | `outputs/seal_checks/seal_final_snapshot.json` |

## 3. Matrix Status by Run

`status=ok` count by run_id is `1` for every run below.

| run_id | label | ok_count | summary |
| --- | --- | --- | --- |
| `20260228_055920_06d6bb_m01` | `seal_mvp01_preft_dense_singlestep` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m01/summary.json` |
| `20260228_055920_06d6bb_m02` | `seal_mvp02_dense_singlestep` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m02/summary.json` |
| `20260228_055920_06d6bb_m03` | `seal_mvp03_bm25_singlestep` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m03/summary.json` |
| `20260228_055920_06d6bb_m04` | `seal_mvp04_hybrid_singlestep` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m04/summary.json` |
| `20260228_055920_06d6bb_m05` | `seal_mvp05_dense_multistep` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m05/summary.json` |
| `20260228_055920_06d6bb_m06` | `seal_mvp06_dense_multistep_t1` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m06/summary.json` |
| `20260228_055920_06d6bb_m07` | `seal_mvp05b_dense_multistep_gate_open` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m07/summary.json` |
| `20260228_055920_06d6bb_m08` | `seal_mvp06b_dense_multistep_t1_gate_open` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m08/summary.json` |
| `20260228_055920_06d6bb_m09` | `seal_mvp05c_dense_multistep_gate_disabled` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m09/summary.json` |
| `20260228_055920_06d6bb_m10` | `seal_mvp06c_dense_multistep_t1_gate_disabled` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m10/summary.json` |
| `20260228_055920_06d6bb_m11` | `seal_mvp07_dense_calc_empty_allow` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m11/summary.json` |
| `20260228_055920_06d6bb_m12` | `seal_mvp08_dense_calc_allow_yoy_diff` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m12/summary.json` |
| `20260228_055920_06d6bb_m13` | `seal_mvp08b_dense_calc_gate_off` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m13/summary.json` |
| `20260228_055920_06d6bb_m14` | `seal_mvp08c_dense_calc_minconf_02` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m14/summary.json` |
| `20260228_055920_06d6bb_m15` | `seal_mvp08d_dense_calc_expand_tasks` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m15/summary.json` |
| `20260228_055920_06d6bb_m16` | `seal_mvp09_dense_multistep_calc` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m16/summary.json` |
| `20260228_055920_06d6bb_m17` | `seal_mvp10_dense_multistep_t1_calc` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m17/summary.json` |
| `20260228_055920_06d6bb_m18` | `seal_mvp11_dense_pqe` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m18/summary.json` |
| `20260228_055920_06d6bb_m19` | `seal_mvp12_dense_pqe_abbrev_only` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m19/summary.json` |
| `20260228_055920_06d6bb_m20` | `seal_mvp13_dense_pqe_calc` | `1` | `outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m20/summary.json` |

## 4. Table and Plot Update Evidence

Tables were updated.

- Previous table timestamp observed before rerun: `2026-02-28 10:43:37`
- New table timestamp after `make_tables`: `2026-02-28 18:33:39`
- Evidence: `docs/TABLE_MAIN.md`, `docs/TABLE_NUMERIC.md`, `docs/TABLE_ABLATION.md`

Plots were updated.

- Previous active seal figure timestamp observed before rerun: `2026-02-28 11:12:44` / `11:12:45`
- New plot timestamp after `plot_all`: `2026-02-28 18:33:40` / `18:33:41`
- Evidence: `thesis/figures_seal/ThemeA/tables/main_results.csv`, `thesis/figures_seal/ThemeA/tables/main_results.tex`, `thesis/figures_seal/ThemeA/figures/ablation_breakdown.pdf`, `thesis/figures_seal/ThemeA/figures/ablation_breakdown.png`, `thesis/figures_seal/FIGURE_CATALOG.md`, `thesis/figures_seal/figures_auto.tex`

Enabled plot data check.

- `outputs/20260228_103340_cb1bb1/logs.txt` shows one enabled figure write: `ablation_breakdown.pdf has_data=True`
- `outputs/seal_checks/seal_final_snapshot.json` records `plot_has_data_false_count = 0` and `plot_has_data_true_count = 1`

## 5. Snapshot Payload

`outputs/seal_checks/seal_final_snapshot.json` includes:

- `commit`
- `matrix_id`
- `matrix_path`
- `plot_run_id`
- `plot_log`
- `status_counts`
- `run_ids`
- per-run `label/run_id/status/summary/logs`
- `tables`
- `figures`
- `plot_has_data_false_count`
- canonical four-command list

## 6. Notes

1. `make_tables.py` has no run-scoped `outputs/<run_id>/logs.txt`, so table regeneration is evidenced by file timestamps/content plus the sealed experiments mapping.
2. The exact `run_matrix_step6` command was started first and created `matrix_id=20260228_055920_06d6bb`. After the terminal wrapper timed out, the remaining runs were completed under the same matrix id and the same seal config set before final matrix metadata was rewritten. The local audit trail remains complete at `outputs/20260228_055920_06d6bb/**`.
3. `plot_all.py` emitted `style_not_found` once, but no enabled figure had `has_data=False`.
4. `thesis/figures_seal/ThemeA/figures/abbrev_breakdown.pdf` and `.png` are older disabled outputs and are not evidence for the current enabled seal plot set.
