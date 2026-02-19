# CALC Closure Report

## 1) Execution Ledger
- Smoke: `python scripts/smoke.py --config configs/smoke.yaml --run-id calc_closure_smoke` (passed).
- Matrix: `python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix configs/tmp_matrix_calc_closure.yaml` with `matrix_id=20260219_034734_85fe50` (`outputs/20260219_034734_85fe50/matrix.json:2`).
- Tables: `python scripts/make_tables.py --experiments configs/step6_experiments_seal.yaml` (closure runs registered at `configs/step6_experiments_seal.yaml:62`).
- Plots: `python scripts/plot_all.py --config scripts/plot_config.yaml` (latest log `outputs/20260219_050026_aa2a85/logs.txt:1`).
- Plot data check: no `has_data=False` in latest plot log; enabled figure record is `has_data=True` (`outputs/20260219_050026_aa2a85/logs.txt:8`).

## 2) C0-C3 Results
| Run | numeric_em | coverage | fallback_ratio | calc_used_vs_fallback_gap |
| --- | --- | --- | --- | --- |
| C0 | 0.3079 | 0.6867 | 0.8544 | 0.3744 |
| C1 | 0.2949 | 0.6502 | 0.9123 | 0.3398 |
| C2 | 0.3525 | 0.6588 | 0.9351 | 0.3838 |
| C3 | 0.3254 | 0.6502 | 0.9298 | 0.3596 |

Evidence:
- Aggregated comparison and threshold flags: `outputs/seal_checks/calc_closure_compare.json:3`, `outputs/seal_checks/calc_closure_compare.json:80`, `outputs/seal_checks/calc_closure_compare.json:111`, `outputs/seal_checks/calc_closure_compare.json:156`.
- Table ingestion in official chain: `docs/TABLE_NUMERIC.md:23`, `docs/TABLE_NUMERIC.md:24`, `docs/TABLE_NUMERIC.md:25`, `docs/TABLE_NUMERIC.md:26`.

## 3) Acceptance Decision
Thresholds (from Prompt 3.5):
- Condition A: `delta numeric_em >= +0.02` and `delta coverage >= -0.03`.
- Condition B: `delta numeric_em >= -0.005` and `delta coverage >= +0.01` and `gap shrink >= +0.05`.
- Guardrail: `delta fallback_ratio <= +0.03`.

Observed:
- `C2` satisfies Condition A (`numeric_em +0.0446`, `coverage -0.0279`) but fails guardrail (`fallback_ratio +0.0807`) (`outputs/seal_checks/calc_closure_compare.json:105`, `outputs/seal_checks/calc_closure_compare.json:106`, `outputs/seal_checks/calc_closure_compare.json:107`, `outputs/seal_checks/calc_closure_compare.json:113`).
- `C1` and `C3` fail A/B and guardrail (`outputs/seal_checks/calc_closure_compare.json:73`, `outputs/seal_checks/calc_closure_compare.json:147`).
- `final_pass_candidates` is empty (`outputs/seal_checks/calc_closure_compare.json:156`).

Decision:
- **Closure success: No**.
- **Chosen state: B) 严谨降级（diagnostic/exploratory module）**.

## 4) Cause Chain (Evidence)
- Baseline diagnosis remains valid: `calc_used` quality is far below fallback (`calc_used em_on_covered=0.0122` vs `fallback em_on_covered=0.3866`) (`outputs/seal_checks/calc_diagnosis_metrics.json:366`, `outputs/seal_checks/calc_diagnosis_metrics.json:370`, `outputs/seal_checks/calc_diagnosis_metrics.json:376`, `outputs/seal_checks/calc_diagnosis_metrics.json:380`).
- D2 conclusion unchanged: extraction strategy is not the primary root cause (`pred_number_changed_qid_count=30`, and `both_wrong_when_pred_changed=30`) (`outputs/seal_checks/calc_diagnosis_metrics.json:870`, `outputs/seal_checks/calc_diagnosis_metrics.json:871`).
- D3 conclusion unchanged: `max_chunks_for_facts=3` is not robust (`coverage` down, only tiny EM change) (`outputs/seal_checks/calc_diagnosis_metrics.json:854`, `outputs/seal_checks/calc_diagnosis_metrics.json:855`, `outputs/seal_checks/calc_diagnosis_metrics.json:856`).
- In closure matrix, `scored_v1` improved numeric_em but increased fallback because `status_insufficient_facts` rose sharply (baseline 16 -> C2 61), causing guardrail failure (`outputs/20260219_034734_85fe50/runs/20260219_034734_85fe50_m01_calc/calc_stats.json:19`, `outputs/20260219_034734_85fe50/runs/20260219_034734_85fe50_m03_calc/calc_stats.json:19`, `outputs/20260219_034734_85fe50/runs/20260219_034734_85fe50_m03_calc/calc_stats.json:4`).
- Top-3 bottlenecks and sampled qids are documented in action plan (`outputs/seal_checks/calc_closure_action_plan.json:12`, `outputs/seal_checks/calc_closure_action_plan.json:16`, `outputs/seal_checks/calc_closure_action_plan.json:36`, `outputs/seal_checks/calc_closure_action_plan.json:56`).

## 5) Implemented Changes (Configurable + Rollback-Safe)
- Task parser v2 and confidence gate in compute path: `src/calculator/compute.py:164`, `src/calculator/compute.py:236`, `src/calculator/compute.py:766`.
- Scored fact selector + audit outputs + per-run stats: `scripts/run_with_calculator.py:283`, `scripts/run_with_calculator.py:495`, `scripts/run_with_calculator.py:724`.
- Schema defaults/types for all new knobs: `src/config/schema.py:48`, `src/config/schema.py:57`, `src/config/schema.py:153`.
- C0-C3 matrix and official table registration: `configs/tmp_matrix_calc_closure.yaml:1`, `configs/step6_experiments_seal.yaml:62`.

## 6) Recommendation (Cost/Benefit)
1. **Stop at rigorous downgrade for this seal cycle**: no candidate passes threshold+guardrail together (`outputs/seal_checks/calc_closure_compare.json:156`).
2. Next highest-yield fix is not further gate tuning; it is reducing `wrong_fact_selection` while preserving calc coverage (current scored selector still increases `status_insufficient_facts`).
3. Keep current implementation as auditable experimental branch (v2 parser + scored selector + `calc_used_records.jsonl`) for future iterations.

## 7) Paper Wording (Rigorous Downgrade)
中文建议（可直接入文）:
- “在当前实现下，Calculator 模块可提升数值覆盖的上界探索能力，但未形成稳定闭环收益。具体表现为：部分配置下 numeric_em 提升，但伴随 fallback_ratio 明显上升，且 calc_used 子集准确率显著低于 fallback 子集，因此总体不满足封装级稳定性要求。我们据此将 Calculator 定位为诊断/探索模块，而非主链路增益模块。”  
- “max_chunks 限制与抽取策略切换（first/result_tag）均未从根因上修复该问题，根因仍是事实选择与任务识别在 calc_used 路径上的质量不足。”

English (optional):
- “In the current implementation, Calculator improves exploratory numeric behavior but does not achieve stable closure-level gains. We observe numeric_em gains in some settings, but with a substantial fallback_ratio increase and a persistent quality gap between calc_used and fallback subsets. Therefore, Calculator is positioned as a diagnostic/exploratory module rather than a sealed production gain module in this cycle.”

## 8) Claim Scope Freeze
- Keep: “Task parser/fact selector are now configurable and auditable.”
- Keep: “Calculator diagnosis pipeline is complete and reproducible.”
- Downgrade to future work: “Calculator delivers stable net numeric gains under seal guardrails.”
- Downgrade to future work: “Calculator can be treated as a packaged core module in Step6 mainline.”
