# SEAL Decision (A4)

Date: 2026-02-18

## Final Conclusion

Decision: **Ready**.

Basis:

1. `subsets_v2` 口径修复已生效并被 Step6 评测链路引用。  
   Evidence: `scripts/build_subsets.py:23`, `scripts/build_subsets.py:55-61`,
   `data/subsets_v2/subsets_stats.json:64-67`,
   `outputs/20260218_120310_8bc565/matrix.json:66-68`.
2. numeric 抽取策略已可控（默认 `first` 兼容旧口径；`result_tag` 可独立审计）。  
   Evidence: `src/config/schema.py:78-84`, `scripts/eval_numeric.py:149-167`,
   `outputs/seal_checks/numeric_extraction_strategy_compare.json:20-24`,
   `outputs/seal_checks/numeric_extraction_strategy_compare.json:267`.
3. PQE 已进入官方表图链路并可见于主表。  
   Evidence: `configs/step6_experiments_seal.yaml:53-60`,
   `docs/TABLE_MAIN.md:20-22`,
   `outputs/seal_checks/pqe_tables_plots_check.json:21-24`.

## Scope Statement

- 主贡献封条范围：`retriever FT + mode ablation + PQE replacement`。  
- calculator 当前作为“交互诊断”模块：观察到 `coverage↑` 同时 `numeric_em↓`，本轮不作为主贡献增益点。  
  Evidence: `outputs/seal_checks/final_gateclear_snapshot.json:157-177`.

## Reproducible Commands

```bash
python scripts/smoke.py --config configs/smoke.yaml --run-id seal_a4_smoke
python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix configs/tmp_matrix_seal_pqe_only.yaml
python scripts/make_tables.py --experiments configs/step6_experiments_seal.yaml
python scripts/plot_all.py --config scripts/plot_config.yaml
```

## Gate-Clear Report

- `docs/SEAL_CHECK_step6_final_gateclear.md`
- `outputs/seal_checks/final_gateclear_snapshot.json`

## Calculator Selective Update (2026-02-19)

- Status: **Not seal-able (selective) in this cycle**.
- Evidence:
  - `docs/CALC_SELECTIVE_CLOSURE_REPORT.md`
  - `outputs/seal_checks/calc_selective_compare.json`
  - `outputs/seal_checks/calc_selective_skip_reason_examples.json`
- Decision rationale:
  - Full-set guardrails fail (`delta_fallback_ratio` > +0.03 in all S1-S3).
  - Full numeric floor fails (`delta_numeric_em` << -0.01).
  - S_calc subset conditions A/B are not met.

CN:
> 本轮 selective calculator 未通过闭环验收。虽然拒用理由分布可解释，但全量 guardrail 与 numeric_em 保底均未通过，因此当前仍定位为诊断模块而非可封装增益模块。

EN:
> The selective calculator does not pass closure acceptance in this cycle. Although skip reasons are interpretable, full-set guardrails and numeric-EM floor both fail, so it remains a diagnostic module rather than a sealable gain module.
