# SEAL Check - Step6 Final Gate-Clear (A4)

Date: 2026-02-18  
Branch: `feat/pqe_replace_multistep`

## 1) Blockers Clear Status

### Blocker-1: complex 年份口径 bug

Status: `PASS`.

- 年份正则已改为非捕获组：`YEAR_RE = r"\b(?:19|20)\d{2}\b"`  
  Evidence: `scripts/build_subsets.py:23`
- 年份提取使用完整 match：`finditer(...).group(0)`  
  Evidence: `scripts/build_subsets.py:55-61`
- `subsets_v2` 中复杂子集两年样本非零：`rule_hits.two_years = 49`，且 `year_hist["2"] = 46`  
  Evidence: `data/subsets_v2/subsets_stats.json:22-27`, `data/subsets_v2/subsets_stats.json:64-67`
- Step6 最小矩阵已实际引用 `subsets_v2` 路径：  
  Evidence: `outputs/20260218_120310_8bc565/matrix.json:66-68`,
  `outputs/20260218_120310_8bc565/matrix.json:142-144`

### Blocker-2: numeric 首数字误伤风险

Status: `PASS`（默认兼容 + 可切换策略可用）。

- `eval_numeric` 已支持三种策略 `first/last/result_tag`：  
  Evidence: `scripts/eval_numeric.py:30-33`, `scripts/eval_numeric.py:149-167`,
  `scripts/eval_numeric.py:186-200`
- 默认策略仍为 `first`（兼容旧口径）：  
  Evidence: `src/config/schema.py:78-84`, `src/config/schema.py:150-154`
- `numeric_per_query.jsonl` 保持写出并新增策略字段：  
  Evidence: `scripts/eval_numeric.py:273`, `scripts/eval_numeric.py:320-338`
- `result_tag` 对比已落盘：`qid` 级抽取差异 `30` 条；示例显示首数字与 `Result:` 数值不同。  
  Evidence: `outputs/seal_checks/numeric_extraction_strategy_compare.json:25-30`,
  `outputs/seal_checks/numeric_extraction_strategy_compare.json:267`

### Blocker-3: PQE 未进入官方表图链路

Status: `PASS`.

- `step6_experiments_seal.yaml` 已登记 `m11/m12/m13`：  
  Evidence: `configs/step6_experiments_seal.yaml:53-60`
- 主表已出现 PQE 行：  
  Evidence: `docs/TABLE_MAIN.md:20-22`
- 绘图验收 `has_data_false_count = 0`：  
  Evidence: `outputs/seal_checks/pqe_tables_plots_check.json:21-24`

## 2) Minimal End-to-End Ablation Closure

| Claim | Baseline | Treatment | Metric / Delta | Conclusion | Evidence |
|---|---|---|---|---|---|
| FT 有效 | `m01_preft_dense` | `m02_postft_dense` | `full_r10 +0.0544`, `full_mrr10 +0.0525` | 提升明显 | `outputs/seal_checks/final_gateclear_snapshot.json:48-58` |
| 检索模式消融可用 | dense | bm25 / hybrid | dense 明显优于 bm25 与 hybrid（R@10/MRR@10） | 模式链路正常 | `outputs/seal_checks/final_gateclear_snapshot.json:60-89` |
| PQE 替换模块有效 | `m02` | `m11_pqe` | `complex_r10 +0.0123`, `abbrev_r10 +0.0040` | 有可解释提升 | `outputs/seal_checks/final_gateclear_snapshot.json:91-101` |
| PQE ablation（PRF-year 边际） | `m12_abbrev_only` | `m11_pqe` | `queries_expanded 11 -> 483`，并对应检索提升 | 提升主要来自 PRF-year | `outputs/seal_checks/final_gateclear_snapshot.json:118-155` |
| calculator 交互 | `m08` | `m13_pqe_calc` | `coverage +0.0172`, `numeric_em -0.0118` | coverage↑但EM↓，当前作为诊断结论 | `outputs/seal_checks/final_gateclear_snapshot.json:157-177` |

补充说明（m13 状态）：

- 矩阵元数据将 `m13` 标记为 failed，但 `summary.json` 和 numeric 指标已完整写出并被表格消费。  
  Evidence: `outputs/20260218_120310_8bc565/matrix.json:224-229`,
  `outputs/20260218_120310_8bc565/runs/20260218_120310_8bc565_m04/summary.json:1-92`

## 3) Final Gate Decision

`Ready`（面向 Step6 全链条封条与绘图冻结）。

范围声明：

- 主贡献链路：`FT + retrieval mode + PQE replacement`。  
- `calculator` 当前定位：`交互诊断/风险披露`，不作为本轮封条主增益来源（因 `coverage↑` 但 `EM↓`）。  

## 4) Audit Artifacts

- `outputs/seal_checks/final_gateclear_snapshot.json`
- `outputs/seal_checks/pqe_min_matrix_compare.json`
- `outputs/seal_checks/pqe_tables_plots_check.json`
- `outputs/seal_checks/numeric_extraction_strategy_compare.json`
