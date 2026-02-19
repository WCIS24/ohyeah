# CALC Selective Closure Report

## 1) Execution Ledger

- Smoke:
  - `python scripts/smoke.py --config configs/smoke.yaml --run-id calc_selective_smoke`
  - Passed (`outputs/calc_selective_smoke/logs.txt`).
- Matrix:
  - `python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix configs/tmp_matrix_calc_selective.yaml`
  - `matrix_id=20260219_104111_d805c6`
- Compare + skip examples:
  - `python scripts/seal_check_calculator_selective.py --matrix-id 20260219_104111_d805c6 --out outputs/seal_checks/calc_selective_compare.json --skip-examples-out outputs/seal_checks/calc_selective_skip_reason_examples.json`
- Tables:
  - `python scripts/make_tables.py --experiments configs/step6_experiments_seal.yaml`
  - Includes S0-S3 rows (`docs/TABLE_NUMERIC.md`).
- Plots:
  - `python scripts/plot_all.py --config scripts/plot_config.yaml`
  - Completed with `ablation_breakdown` updated.

## 2) S0-S3 Full Metrics

Source: `outputs/seal_checks/calc_selective_compare.json`

| Role | Label | numeric_em | coverage | fallback_ratio | delta_fallback_ratio vs S0 | full guardrail |
| --- | --- | --- | --- | --- | --- | --- |
| S0 | calc_selective_s0_baseline | 0.3079 | 0.6867 | 0.8240 | +0.0000 | Pass |
| S1 | calc_selective_s1_pre_gate_only | 0.1131 | 0.6073 | 0.8884 | +0.0644 | **Fail** |
| S2 | calc_selective_s2_strict_gates | 0.1062 | 0.6052 | 0.8927 | +0.0687 | **Fail** |
| S3 | calc_selective_s3_strict_plus_lookup | 0.1099 | 0.6052 | 0.8906 | +0.0665 | **Fail** |

Full-set thresholds:
- Guardrail: `delta_fallback_ratio <= +0.03`
- Numeric floor: `delta_numeric_em >= -0.01`
- Coverage floor: `delta_coverage >= -0.05`

Result: all selective runs fail full-set acceptance.

## 3) S_calc Subset Metrics

S_calc definition: `needs_calc == 1` (query-level detector); baseline S0 subset aligned by reference needs_calc set.

| Role | S_calc count | numeric_em | coverage | calculator_used_ratio | gap_shrink vs S0 |
| --- | --- | --- | --- | --- | --- |
| S0 | 120 | 0.2667 | 0.8583 | 0.6833 | 0.0000 |
| S1 | 120 | 0.0583 | 0.8083 | 0.4333 | +0.2952 |
| S2 | 120 | 0.0417 | 0.8000 | 0.4167 | +0.2592 |
| S3 | 120 | 0.0500 | 0.8000 | 0.4250 | +0.2764 |

Subset acceptance rules:
- A: `delta_numeric_em >= +0.03` and `gap_shrink >= +0.03`
- B: `delta_coverage >= +0.03` and `gap_shrink >= +0.02` and full guardrail pass

Result: none of S1-S3 passes A or B.

## 4) Skip-Reason Diagnostics

- Compare JSON: `outputs/seal_checks/calc_selective_compare.json`
- Example buckets: `outputs/seal_checks/calc_selective_skip_reason_examples.json`
- Reason buckets with >=20 qids:
  - `pre_gate`: 437 available, 20 returned
  - `evidence_gate`: 77 available, 20 returned
  - `compute_fail`: 77 available, 20 returned
- Low-frequency bucket:
  - `post_gate`: 2 available (listed under `omitted_reasons_lt_min_examples`)

## 5) Threshold Decision

- Selective closure success: **No**
- Final pass candidates: `[]`
- Main blockers:
  - Full guardrail violation on fallback ratio (+0.0644 to +0.0687 vs threshold +0.03).
  - Large full numeric EM regression (about -0.20 vs S0).
  - S_calc numeric_em regression in all selective runs.

## 6) Rigorous Downgrade Wording (Paper-ready)

CN:
> 本轮 selective calculator 未达到闭环标准。虽然 skip reason 分布可解释，且在子集上 `gap_shrink` 有所改善，但全量 guardrail（尤其 fallback_ratio）与 numeric_em 保底均未通过。基于当前证据，calculator 更适合作为诊断模块与路由分析工具，而非可封装的稳定增益模块。

EN:
> The selective calculator does not meet closure criteria in this cycle. Although skip-reason behavior is interpretable and subset gap-shrink improves, full-set guardrails (especially fallback-ratio) and the numeric-EM floor both fail. Based on current evidence, the calculator is better positioned as a diagnostic/routing analysis module rather than a sealable production gain module.

## 7) Artifacts

- Root cause memo: `docs/CALC_SELECTIVE_ROOTCAUSE.md`
- Closure report: `docs/CALC_SELECTIVE_CLOSURE_REPORT.md`
- Machine-readable compare: `outputs/seal_checks/calc_selective_compare.json`
- Skip reason examples: `outputs/seal_checks/calc_selective_skip_reason_examples.json`
