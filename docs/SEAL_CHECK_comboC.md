# SEAL Check: comboC

## Scope

- Matrix run: `20260228_012006_b44483`
- plot_all run: `20260228_031244_cef6dc`
- Selected runs:
  - `comboC_s0_baseline_b_legacy` -> `20260228_012006_b44483/runs/20260228_012006_b44483_m01`
  - `comboC_s1_a_only_template` -> `20260228_012006_b44483/runs/20260228_012006_b44483_m02`
  - `comboC_s2_b_only_combo` -> `20260228_012006_b44483/runs/20260228_012006_b44483_m03`
  - `comboC_s3_c_full_template` -> `20260228_012006_b44483/runs/20260228_012006_b44483_m04`
  - `comboC_s4_c_filter_tight` -> `20260228_012006_b44483/runs/20260228_012006_b44483_m07`

## Reproduction

```powershell
python scripts/build_calc_needed_subset.py --config configs/build_calc_needed_subset.yaml
python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix configs/step6_matrix_comboC.yaml
python scripts/make_tables.py --experiments configs/step6_experiments_seal.yaml
python scripts/plot_all.py --config scripts/plot_config.yaml
Get-ChildItem outputs/comboC_eval_cfgs/*.yaml | Sort-Object Name | ForEach-Object {
  python scripts/eval_numeric.py --config $_.FullName
}
```

## Official Table/Figure Chain

- `plot_all` succeeded from `scripts/plot_config.yaml`.
- `main_results` table was generated with `rows=33`.
- `ablation_breakdown` was generated with `has_data=True`.
- Output roots:
  - `thesis/figures_seal/ThemeA/tables/main_results.csv`
  - `thesis/figures_seal/ThemeA/tables/main_results.tex`
  - `thesis/figures_seal/ThemeA/figures/ablation_breakdown.pdf`
  - `thesis/figures_seal/ThemeA/figures/ablation_breakdown.png`

Local evidence:

- `outputs/20260228_031244_cef6dc/logs.txt`
- `thesis/figures_seal/FIGURE_CATALOG.md`

## Submission Evidence

- Main table: `docs/TABLE_MAIN.md`
- Numeric table: `docs/TABLE_NUMERIC.md`
- Ablation table: `docs/TABLE_ABLATION.md`

The table schema is unchanged. comboC rows were appended without replacing earlier SEAL rows.

## Full Table Check

`docs/TABLE_MAIN.md` still contains the earlier full-eval SEAL runs unchanged. The new comboC rows are additive only.

Important limitation:

- The mini-matrix was run with `eval.skip_retrieval=true`.
- Therefore the comboC rows appear in `TABLE_MAIN` with retrieval columns as `-`.
- This is a structural chain check, not evidence of retrieval improvement.

## dev_numeric Comparison

From `docs/TABLE_NUMERIC.md`:

| label | num_em | num_cov | vs baseline |
| --- | ---: | ---: | --- |
| comboC_s0_baseline_b_legacy | 0.3079 | 0.6867 | baseline |
| comboC_s1_a_only_template | 0.1416 | 0.7597 | cov `+0.0730`, em `-0.1663` |
| comboC_s2_b_only_combo | 0.3079 | 0.6867 | identical |
| comboC_s3_c_full_template | 0.1329 | 0.7554 | cov `+0.0687`, em `-0.1750` |
| comboC_s4_c_filter_tight | 0.1360 | 0.7554 | cov `+0.0687`, em `-0.1719` |

Result:

- `B-only` is a compatibility check. It matches baseline on global numeric metrics.
- `A-only` and `C` increase coverage, but both regress `numeric_em`.
- Under the current mini-matrix, no comboC candidate improves both `num_em` and `num_cov` on `dev_numeric`.

## Subset Check

Subset definitions were built from query only:

- `data/subsets/dev_calc_needed_qids.txt`
- `data/subsets/dev_value_needed_qids.txt`

Consolidated subset results:

- `outputs/seal_checks/comboC_subset_eval_summary.json`

### S_calc

| label | numeric_em | coverage | delta_em vs baseline | delta_cov vs baseline |
| --- | ---: | ---: | ---: | ---: |
| baseline | 0.2903 | 0.7701 | 0.0000 | 0.0000 |
| A-only | 0.2029 | 0.8621 | -0.0874 | +0.0920 |
| B-only | 0.2903 | 0.7701 | 0.0000 | 0.0000 |
| C full | 0.1884 | 0.8621 | -0.1019 | +0.0920 |
| C filter tight | 0.1884 | 0.8621 | -0.1019 | +0.0920 |

### S_value

| label | numeric_em | coverage | delta_em vs baseline | delta_cov vs baseline |
| --- | ---: | ---: | ---: | ---: |
| baseline | 0.3988 | 0.8265 | 0.0000 | 0.0000 |
| A-only | 0.1237 | 0.9817 | -0.2751 | +0.1553 |
| B-only | 0.3988 | 0.8265 | 0.0000 | 0.0000 |
| C full | 0.1135 | 0.9726 | -0.2853 | +0.1461 |
| C filter tight | 0.1189 | 0.9726 | -0.2799 | +0.1461 |

Result:

- Query-only subsets are reproducible and avoid gold leakage.
- `B-only` again matches baseline exactly.
- `A-only` and `C` improve coverage on both subsets, but the `numeric_em` loss is large.
- On this evaluation, comboC does not deliver positive subset net gain over baseline.

## Auditability

Key audit files:

- Baseline: `outputs/20260228_012006_b44483/runs/20260228_012006_b44483_m01_calc/calc_audit.json`
- A-only: `outputs/20260228_012006_b44483/runs/20260228_012006_b44483_m02_calc/calc_audit.json`
- C full: `outputs/20260228_012006_b44483/runs/20260228_012006_b44483_m04_calc/calc_audit.json`
- C filter tight: `outputs/20260228_012006_b44483/runs/20260228_012006_b44483_m07_calc/calc_audit.json`

Observed distributions:

- Baseline (`m01`):
  - `used_module_counts = {"B": 570}`
  - `route_reason_counts = {"combo_disabled": 570}`
  - `fallback_mode_counts = {"template": 487, "none": 83}`
- A-only (`m02`):
  - `used_module_counts = {"A": 282, "NONE": 288}`
  - `reject_reason_counts = {"no_numeric_intent": 282, "no_facts": 5, "a_conf_below_tau": 1}`
- C full (`m04`):
  - `used_module_counts = {"A": 280, "B": 290}`
  - `route_reason_counts = {"value_ok": 280, "no_numeric_intent_to_b": 282, "no_facts_to_b": 7, "a_conf_below_tau_to_b": 1}`
  - `fact_filter.kept_ratio = 0.2116`
- C filter tight (`m07`):
  - `used_module_counts = {"A": 280, "B": 290}`
  - same route reason pattern as `m04`
  - `fact_filter.kept_ratio = 0.1210`

Interpretation:

- The route is auditable at per-run level.
- Most A rejections come from `no_numeric_intent`, not from threshold tuning.
- Tightening the fact filter reduces retained facts materially, but does not recover `numeric_em`.

## Conclusion

- comboC has entered the official Step6 table/figure chain successfully.
- The chain is submission-ready in the sense that `TABLE_*` and `plot_all` artifacts are generated and locally auditable.
- The current mini-matrix does not justify replacing the baseline:
  - `B-only` is a no-op compatibility control.
  - `A-only` and `C` raise coverage but regress `numeric_em` on both global and subset checks.
- The local audit trail is sufficient for CI or offline review without relying on GitHub-hosted outputs.
