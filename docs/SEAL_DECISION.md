# SEAL Decision (A1-A7 Final)

Date: 2026-02-18  
Scope: final seal decision based on A1-A7 evidence artifacts in `docs/SEAL_CHECK_*` and `outputs/`.

## 1) Final conclusions

Conclusion 1 (enter plotting stage?): **No**.

Top 3 blocking reasons:
1. Calculator branch is still near full fallback in the patched run (`gate_task=465/570`,
   fallback total `490/570`), so calculator effectiveness is not closed.
   Evidence: `outputs/20260218_012802_326769/runs/20260218_012802_326769_m01_calc/calc_stats.json:17`,
   `outputs/20260218_012802_326769/runs/20260218_012802_326769_m01_calc/calc_stats.json:16`.
2. Multistep gain is too small to claim module effectiveness (`avg_steps=1.081` with strong gate block;
   retrieval delta ~0.0001-0.0003 in A5 audit).
   Evidence: `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05_ms/logs.txt:8`,
   `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05_ms/logs.txt:9`,
   `docs/SEAL_CHECK_step4_step5_ablation.md:58`.
3. A5 ablation closure itself is marked partial/not qualified for seal.
   Evidence: `docs/SEAL_CHECK_step4_step5_ablation.md:8`,
   `docs/SEAL_CHECK_step4_step5_ablation.md:15`,
   `docs/SEAL_CHECK_step4_step5_ablation.md:103`.

Conclusion 2 (action type): **No => execute minimal closure plan** (6 actions below).

---

## 2) Seal checklist (verifiable)

| Checklist item | Status | Evidence |
|---|---|---|
| A1 ledger exists and maps Step0-Step7 to repo-equivalent flow | PASS | `docs/SEAL_LEDGER.md:12`, `docs/SEAL_LEDGER.md:17` |
| Step0/Step1 env+smoke gate passes | PASS | `docs/SEAL_CHECK_step0_step1.md:8`, `docs/SEAL_CHECK_step0_step1.md:102` |
| Subset pipeline (`complex/abbrev/numeric`) wired and consumed in main eval | PASS | `docs/SEAL_CHECK_step2_subsets.md:9`, `docs/SEAL_CHECK_step2_subsets.md:84`, `docs/SEAL_CHECK_step2_subsets.md:110` |
| Retriever pre-FT vs post-FT chain is traceable | PASS | `docs/SEAL_CHECK_step3_retriever.md:10`, `docs/SEAL_CHECK_step3_retriever.md:68`, `docs/SEAL_CHECK_step3_retriever.md:87` |
| Step6 matrix traceability metadata exists (`matrix.json`, run metadata) | PASS | `outputs/20260217_123645_68f6b9/matrix.json:2`, `outputs/20260217_123645_68f6b9/matrix.json:4`, `outputs/20260217_123645_68f6b9/matrix.json:6` |
| Step6 tables are reproducible and aligned with seal experiments | PASS | `docs/SEAL_CHECK_step6_tables.md:8`, `docs/SEAL_CHECK_step6_tables.md:114`, `docs/SEAL_CHECK_step6_tables.md:120` |
| Step7 plotting chain (enabled items) is stable (`has_data=True`) | PASS | `docs/SEAL_CHECK_step7_plots.md:9`, `docs/SEAL_CHECK_step7_plots.md:44`, `docs/SEAL_CHECK_step7_plots.md:45` |
| dense/bm25/hybrid contrast closed | PASS | `docs/SEAL_CHECK_step4_step5_ablation.md:57` |
| Multistep on/off and depth effectiveness closed | FAIL | `docs/SEAL_CHECK_step4_step5_ablation.md:14`, `docs/SEAL_CHECK_step4_step5_ablation.md:58`, `docs/SEAL_CHECK_step4_step5_ablation.md:59` |
| Calculator gate effectiveness closed (not near full fallback) | FAIL | `docs/SEAL_CHECK_step4_step5_ablation.md:15`, `docs/SEAL_CHECK_step4_step5_ablation.md:92`, `docs/SEAL_CHECK_step4_step5_ablation.md:103` |

Seal decision rule used here:
- If any key module-closure checklist fails (multistep or calculator), decision is `No`.

---

## 3) Minimal closure plan (max 6 actions)

### Action 1 - Add calculator gate-off diagnostic control

- Patch:
  - Edit `configs/step6_matrix_seal.yaml` to add `seal_mvp08b_dense_calc_gate_off`
    with same settings as `seal_mvp08_dense_calc_allow_yoy_diff` plus:
    `calculator.gate.enabled=false`.
  - Add corresponding entry to `configs/step6_experiments_seal.yaml`.
- Verify command:

```bash
python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix configs/step6_matrix_seal.yaml
```

- Rerun set: new run `m08b` only (or an isolated one-run matrix file if you want strict minimal rerun).
- Pass criterion:
  - `calc_stats.json` exists and fallback drops materially vs `m08`.
  - Compare `gate_task` and total fallback against
    `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08_calc/calc_stats.json:16`.

### Action 2 - Add one tuned calculator gate run

- Patch:
  - Add `seal_mvp08c_dense_calc_tuned_gate` in `configs/step6_matrix_seal.yaml` with
    same base as `m08`, then tune one gate factor at a time (example first step:
    `calculator.gate.min_conf=0.2`; keep allow list unchanged).
  - Keep `scripts/run_with_calculator.py` logic unchanged; tuning is config-only
    against gate logic at `scripts/run_with_calculator.py:252` to `scripts/run_with_calculator.py:269`.
- Verify command:

```bash
python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix configs/step6_matrix_seal.yaml
```

- Rerun set: `m08c` only.
- Pass criterion:
  - fallback total < 70% and `numeric_dev.coverage` does not regress vs `m08`.

### Action 3 - Add multistep activation diagnostic pair

- Patch:
  - In `configs/step6_matrix_seal.yaml`, add pair `m05b`/`m06b`:
    - same as `m05`/`m06` but set `multistep.gate.min_gap_conf=0.0`
      (or `multistep.gate.enabled=false` for a pure activation check).
- Verify command:

```bash
python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix configs/step6_matrix_seal.yaml
```

- Rerun set: `m05b`, `m06b`.
- Pass criterion:
  - `avg_steps` clearly > 1 for `m05b` and improvement over `m06b` is visible on at least one
    retrieval metric (`full_mrr10` or `complex_mrr10` >= +0.005).

### Action 4 - Freeze post-FT model path (remove moving target)

- Patch:
  - Replace `models/retriever_ft/latest` with immutable model path
    (for current seal: `models/retriever_ft/20260203_005729_cd195e`) in
    `configs/step6_matrix_seal.yaml` entries now using line positions around
    `configs/step6_matrix_seal.yaml:14`, `configs/step6_matrix_seal.yaml:23`, `configs/step6_matrix_seal.yaml:32`.
- Verify command:

```bash
python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix configs/step6_matrix_seal.yaml
```

- Rerun set: any newly added closure runs (`m08b/m08c/m05b/m06b`), not all 10.
- Pass criterion:
  - New matrix metadata commands contain immutable path (check `matrix.json` command payload).

### Action 5 - Refresh table artifacts for closure runs

- Patch:
  - Update `configs/step6_experiments_seal.yaml` to include new closure runs and intended groups.
- Verify command:

```bash
python scripts/make_tables.py --experiments configs/step6_experiments_seal.yaml
```

- Rerun set: none (table generation only).
- Pass criterion:
  - `docs/TABLE_MAIN.md`, `docs/TABLE_NUMERIC.md`, `docs/TABLE_ABLATION.md`
    include new run IDs and remain order-consistent.

### Action 6 - Re-run plotting acceptance after closure rows are in tables

- Patch:
  - No code patch required unless you want extra plots enabled.
  - Keep disabled optional plots unless their data contracts are satisfied
    (see `docs/SEAL_CHECK_step7_plots.md:78` onward).
- Verify command:

```bash
python scripts/plot_all.py --config scripts/plot_config.yaml
```

- Rerun set: none (plot generation only).
- Pass criterion:
  - Enabled items still `has_data=True` and updated figure/table files are generated.

---

## 4) Recommended post-seal directory layout

Use a single sealed release bundle (example):

```text
results/
  seal_20260218/
    matrix/
      matrix.json
      experiments_resolved.yaml
      runs/
        <run_id>/summary.json
        <run_id>/config.resolved.yaml
        <run_id>/git_commit.txt
    tables/
      TABLE_MAIN.md
      TABLE_NUMERIC.md
      TABLE_ABLATION.md
    figures/
      ThemeA/
        tables/main_results.csv
        tables/main_results.tex
        figures/ablation_breakdown.pdf
    reproduce/
      step6_matrix_seal.yaml
      step6_experiments_seal.yaml
      plot_config.yaml
      README_reproduce.txt
```

---

## 5) Reproducible entry points (top 3)

```bash
python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix configs/step6_matrix_seal.yaml
python scripts/make_tables.py --experiments configs/step6_experiments_seal.yaml
python scripts/plot_all.py --config scripts/plot_config.yaml
```

---

## 6) Risk statement

1. Retriever model pointer drift has been mitigated by Action 4
   (`latest` -> immutable version path), but historical runs still used `latest`.
   Evidence: `configs/step6_matrix_seal.yaml:14`,
   `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m05_ms/logs.txt:5`.
2. Calculator numeric gains are currently confounded by heavy fallback gating;
   results can flip with small gate changes.
   Evidence: `outputs/20260217_123645_68f6b9/runs/20260217_123645_68f6b9_m08_calc/calc_stats.json:16`.
3. Multistep is seed-stable in current run set but effect size is very small and may
   be statistically fragile for claims.
   Evidence: `docs/SEAL_CHECK_step4_step5_ablation.md:58`.
4. Plot style config points to missing style assets; not blocking, but visual style
   is not sealed.
   Evidence: `scripts/plot_config.yaml:2`, `outputs/20260217_171347_e4ead5/logs.txt:6`.

---

## 7) Decision summary

- Current seal decision: **No**.
- Move to final plotting freeze only after the 6 closure actions above pass their checks.

---

## 8) Execution update (Action 1 done)

Action executed:
- Added `seal_mvp08b_dense_calc_gate_off` to
  `configs/step6_matrix_seal.yaml`.
- Ran smoke precheck:
  `python scripts/smoke.py --config configs/smoke.yaml --run-id a8_action1_smoke`
  (evidence: `outputs/a8_action1_smoke/logs.txt:1`).
- Ran one-run matrix:
  `python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix outputs/tmp_matrix_action1_m08b.yaml`.

Run artifacts:
- matrix: `outputs/20260217_174322_d71045/matrix.json:2`
- new run: `outputs/20260217_174322_d71045/runs/20260217_174322_d71045_m01/summary.json:2`
- calc stats: `outputs/20260217_174322_d71045/runs/20260217_174322_d71045_m01_calc/calc_stats.json:2`

m08 vs m08b comparison (computed):
- `gate_task` ratio: `0.815789 -> 0.000000`
- fallback total ratio: `0.859649 -> 0.800000`
- numeric coverage: `0.669528 -> 0.682403`
- numeric EM: `0.319728 -> 0.286667`

Evidence log:
- `outputs/seal_checks/action1_m08_vs_m08b_compare.log:3` to
  `outputs/seal_checks/action1_m08_vs_m08b_compare.log:14`

---

## 9) Execution update (Action 2 done, but failed to close)

Action executed:
- Added `seal_mvp08c_dense_calc_minconf_02` to
  `configs/step6_matrix_seal.yaml`.
- Ran smoke precheck:
  `python scripts/smoke.py --config configs/smoke.yaml --run-id a8_action2_smoke`
  (evidence: `outputs/a8_action2_smoke/logs.txt:1`).
- Ran one-run matrix:
  `python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix outputs/tmp_matrix_action2_m08c.yaml`.

Run artifacts:
- matrix: `outputs/20260218_012802_326769/matrix.json:2`
- new run: `outputs/20260218_012802_326769/runs/20260218_012802_326769_m01/summary.json:2`
- calc stats: `outputs/20260218_012802_326769/runs/20260218_012802_326769_m01_calc/calc_stats.json:2`

m08 vs m08c comparison (computed):
- `gate_task` ratio: `0.815789 -> 0.815789` (no change)
- fallback total ratio: `0.859649 -> 0.859649` (no change)
- numeric coverage: `0.669528 -> 0.669528` (no change)
- numeric EM: `0.319728 -> 0.319728` (no change)

Evidence log:
- `outputs/seal_checks/action2_m08_m08b_m08c_compare.log:2`
- `outputs/seal_checks/action2_m08_m08b_m08c_compare.log:4`

Status impact:
- Action2 did not reduce calculator fallback bottleneck, so global seal decision remains `No`.

---

## 10) Execution update (Action 3 done, not closing multistep)

Action executed:
- Added `seal_mvp05b_dense_multistep_gate_open` and
  `seal_mvp06b_dense_multistep_t1_gate_open` in `configs/step6_matrix_seal.yaml`
  with `multistep.gate.min_gap_conf=0.0`.
- Ran smoke precheck:
  `python scripts/smoke.py --config configs/smoke.yaml --run-id a9_action3_smoke`
  (evidence: `outputs/a9_action3_smoke/logs.txt:1`).
- Ran pair matrix:
  `python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix outputs/tmp_matrix_action3_m05b_m06b.yaml`.

Run artifacts:
- matrix: `outputs/20260218_023916_906096/matrix.json:2`
- m05b summary: `outputs/20260218_023916_906096/runs/20260218_023916_906096_m01/summary.json:2`
- m06b summary: `outputs/20260218_023916_906096/runs/20260218_023916_906096_m02/summary.json:2`

m05/m06 vs m05b/m06b comparison:
- m05 full/complex MRR@10 unchanged:
  `0.255595 / 0.296471` -> `0.255595 / 0.296471`
- m06 full/complex MRR@10 unchanged:
  `0.255448 / 0.296128` -> `0.255448 / 0.296128`
- avg_steps unchanged:
  `m05 1.081 -> m05b 1.081`, `m06 1.000 -> m06b 1.000`

Evidence:
- `outputs/seal_checks/action3_multistep_compare.json:2`
- `outputs/seal_checks/action3_multistep_compare.json:47`

Status impact:
- Action3 executed successfully, but did not improve multistep effect size.

---

## 11) Execution update (Action 4/5/6 done)

Action 4 (lock retriever path):
- Replaced all `models/retriever_ft/latest` in seal matrix with immutable
  `models/retriever_ft/20260203_005729_cd195e`.
- Evidence: `configs/step6_matrix_seal.yaml:14`,
  `configs/step6_matrix_seal.yaml:41`,
  `configs/step6_matrix_seal.yaml:154`.

Action 5 (update experiments + regenerate tables):
- Updated `configs/step6_experiments_seal.yaml` with new runs:
  `m05b`, `m06b`, `m08c`.
- Evidence: `configs/step6_experiments_seal.yaml:20`,
  `configs/step6_experiments_seal.yaml:23`,
  `configs/step6_experiments_seal.yaml:35`.
- Ran:
  `python scripts/make_tables.py --experiments configs/step6_experiments_seal.yaml`
- Table evidence:
  `docs/TABLE_MAIN.md:9`,
  `docs/TABLE_ABLATION.md:4`,
  `docs/TABLE_NUMERIC.md:14`.

Action 6 (plot_all acceptance):
- Ran:
  `python scripts/plot_all.py --config scripts/plot_config.yaml`
- Enabled figure has data:
  `outputs/20260218_024755_ad935b/logs.txt:8` (`has_data=True`).
- Main result table rendered with 14 runs:
  `outputs/20260218_024755_ad935b/logs.txt:7`.
- Disabled figures remain disabled by config (not a failure):
  `scripts/plot_config.yaml:46`,
  `scripts/plot_config.yaml:54`,
  `scripts/plot_config.yaml:66`,
  `scripts/plot_config.yaml:73`,
  `scripts/plot_config.yaml:80`.

---

## 12) Decision refresh after Action 3-6

- Traceability, tables, plotting, and model path freeze are now in good state.
- Core closure still fails on two scientific gates:
  1) calculator fallback remains high (`m08`/`m08c`);
  2) multistep ablation effect remains negligible (`m05/m06` vs `m05b/m06b`).

Final seal decision remains: **No**.
