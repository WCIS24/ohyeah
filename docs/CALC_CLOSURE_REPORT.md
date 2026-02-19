# CALC Closure Report (Round-2: soft fallback + retry)

## 1) Execution Ledger
- Smoke:
  - `python scripts/smoke.py --config configs/smoke.yaml --run-id calc_closure_smoke`
  - Passed (`outputs/calc_closure_smoke/logs.txt`).
- Matrix:
  - `python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix configs/step6_matrix_calc_closure_v1.yaml`
  - `matrix_id=20260219_071245_dd1cc7` (`outputs/20260219_071245_dd1cc7/matrix.json:3`).
- Tables:
  - `python scripts/make_tables.py --experiments configs/step6_experiments_seal.yaml`
  - Closure rows are in official table chain (`docs/TABLE_NUMERIC.md:23`, `docs/TABLE_NUMERIC.md:26`).
- Plots:
  - `python scripts/plot_all.py --config scripts/plot_config.yaml`
  - Latest plot log has `has_data=True` and no `has_data=False` (`outputs/20260219_082628_c7ccb8/logs.txt:8`).

## 2) Patch Scope (Backward-Compatible)
- Policy-based compute retry path (default unchanged when `policy=None`):
  - `src/calculator/compute.py:874`
  - `src/calculator/compute.py:963`
  - `src/calculator/compute.py:1065`
- Scored selector top-groups + soft fallback wiring:
  - `scripts/run_with_calculator.py:324`
  - `scripts/run_with_calculator.py:518`
  - `scripts/run_with_calculator.py:657`
- Numeric diagnostics appended (without removing legacy metrics):
  - `scripts/eval_numeric.py:396`
  - `scripts/eval_numeric.py:404`
- New schema keys (default no behavior change):
  - `src/config/schema.py:68`
  - `src/config/schema.py:171`
- New closure matrix:
  - `configs/step6_matrix_calc_closure_v1.yaml:2`
  - `configs/step6_matrix_calc_closure_v1.yaml:83`

## 3) C0-C3 Comparison
Source: `outputs/seal_checks/calc_closure_compare.json:1`

| Role | Label | numeric_em | coverage | fallback_ratio | gap_shrink vs C0 | A | B | Guardrail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C0 | calc_closure_c0_baseline | 0.3079 | 0.6867 | 0.8240 | 0.0000 | N/A | N/A | Pass |
| C1 | calc_closure_c1_scored_hard | 0.3423 | 0.6695 | 0.9034 | -0.0077 | Pass | Fail | **Fail** |
| C2 | calc_closure_c2_scored_soft | 0.3113 | 0.6867 | 0.8240 | -0.0042 | Fail | Fail | Pass |
| C3 | calc_closure_c3_scored_soft_retry | 0.3113 | 0.6867 | 0.8262 | -0.0189 | Fail | Fail | Pass |

Threshold definitions:
- Condition A: `delta_numeric_em >= +0.02` and `delta_coverage >= -0.03` (`outputs/seal_checks/calc_closure_compare.json:6`)
- Condition B: `delta_numeric_em >= -0.005` and `delta_coverage >= +0.01` and `gap_shrink >= +0.05` (`outputs/seal_checks/calc_closure_compare.json:7`)
- Guardrail: `delta_fallback_ratio <= +0.03` (`outputs/seal_checks/calc_closure_compare.json:8`)

## 4) Decision (Binary)
- **Closure success: No**
- Evidence:
  - No pass candidate (`outputs/seal_checks/calc_closure_compare.json:169`)
  - C1 meets A but violates guardrail: `delta_fallback_ratio=+0.0794` (`outputs/seal_checks/calc_closure_compare.json:79`, `outputs/seal_checks/calc_closure_compare.json:85`)
  - C2/C3 keep guardrail but fail A/B and do not shrink calc-used quality gap (`outputs/seal_checks/calc_closure_compare.json:116`, `outputs/seal_checks/calc_closure_compare.json:119`, `outputs/seal_checks/calc_closure_compare.json:158`)

## 5) Why It Still Does Not Close (Top-2)
1. `calc_used` quality gap still not shrinking.
   - `gap_shrink` is negative for C1/C2/C3 (`outputs/seal_checks/calc_closure_compare.json:80`, `outputs/seal_checks/calc_closure_compare.json:119`, `outputs/seal_checks/calc_closure_compare.json:158`).
2. Hard scored selector still increases fallback pressure when no soft path.
   - C1 `insufficient_facts=52` vs C0 `17` (`outputs/20260219_071245_dd1cc7/runs/20260219_071245_dd1cc7_m02_calc/calc_stats.json:7`, `outputs/20260219_071245_dd1cc7/runs/20260219_071245_dd1cc7_m01_calc/calc_stats.json:7`).

## 6) Soft Fallback Effect (What Improved)
- C2/C3 soft fallback avoided the C1-style collapse:
  - C2 fallback_ratio returned to baseline (`outputs/seal_checks/calc_closure_compare.json:101`, `outputs/seal_checks/calc_closure_compare.json:118`)
  - Soft fallback activated:
    - C2 attempts/hits: `479/50` (`outputs/20260219_071245_dd1cc7/runs/20260219_071245_dd1cc7_m03_calc/calc_stats.json:72`)
    - C3 attempts/hits: `461/34` (`outputs/20260219_071245_dd1cc7/runs/20260219_071245_dd1cc7_m04_calc/calc_stats.json:70`)
- But closure target was not reached because gap did not improve.

## 7) Rigorous Downgrade (for paper)
Recommended claim scope:
- Keep: calculator pipeline is now configurable and auditable (`task_parser`, `selector`, `execution`, per-query route fields).
- Keep: we can reduce hard-failure side effects via soft fallback.
- Downgrade: do not claim stable net numeric closure gain in this cycle.

Suggested wording (CN):
> 当前 calculator 版本在部分设置下可以提升 numeric_em，但尚未在统一 guardrail 下形成稳定闭环收益。核心原因是 calc_used 子路径准确率与 fallback 子路径仍存在稳定差距，且该差距在本轮 closure 对照中未显著收敛。因此我们将 calculator 定位为诊断/探索模块，而非主链路封装增益模块。

Suggested wording (EN):
> In this cycle, the calculator shows improvements on selected settings but does not deliver stable closure-level gains under the guardrail constraints. The core issue is a persistent quality gap between the calc-used and fallback routes, which did not shrink in the closure matrix. We therefore position the current calculator as a diagnostic/exploratory module rather than a sealed production gain module.

## 8) Output Artifacts
- Compare JSON: `outputs/seal_checks/calc_closure_compare.json`
- Matrix metadata: `outputs/20260219_071245_dd1cc7/matrix.json`
- Resolved matrix mapping: `outputs/20260219_071245_dd1cc7/experiments_resolved.yaml`
- Official table rows: `docs/TABLE_NUMERIC.md:23`
