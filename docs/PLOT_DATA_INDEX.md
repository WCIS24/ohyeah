# Plot Data Index

## 说明

本文件记录“字段 -> 来源 -> 脚本 -> 生成路径”的对应关系，目的是保证后续画图不需要重新翻代码定位数据。

字段来源分两类：

- `commit-safe`：可直接由仓库文档或 seal 图表产物核验。
- `local-only`：来自 `outputs/**` 或 `data/**` 的本地审计文件，不可远端直接核验。

## A. Retrieval 主结果字段

| 字段 | 含义 | 来源级别 | 来源文件 | 上游脚本 | 当前生成路径 / 表面 |
| --- | --- | --- | --- | --- | --- |
| `full_r10` | 全集 Recall@10 | commit-safe | `docs/TABLE_MAIN.md` | `scripts/make_tables.py` | `docs/TABLE_MAIN.md` |
| `full_mrr10` | 全集 MRR@10 | commit-safe | `docs/TABLE_MAIN.md` | `scripts/make_tables.py` | `docs/TABLE_MAIN.md` |
| `complex_r10` | 复杂子集 Recall@10 | commit-safe | `docs/TABLE_MAIN.md` | `scripts/make_tables.py` | `docs/TABLE_MAIN.md` |
| `complex_mrr10` | 复杂子集 MRR@10 | commit-safe | `docs/TABLE_MAIN.md` | `scripts/make_tables.py` | `docs/TABLE_MAIN.md` |
| `abbrev_r10` | 缩写子集 Recall@10 | commit-safe | `docs/TABLE_MAIN.md` | `scripts/make_tables.py` | `docs/TABLE_MAIN.md` |
| `abbrev_mrr10` | 缩写子集 MRR@10 | commit-safe | `docs/TABLE_MAIN.md` | `scripts/make_tables.py` | `docs/TABLE_MAIN.md` |

## B. Numeric 字段

| 字段 | 含义 | 来源级别 | 来源文件 | 上游脚本 | 当前生成路径 / 表面 |
| --- | --- | --- | --- | --- | --- |
| `num_em` | numeric exact match | commit-safe | `docs/TABLE_NUMERIC.md` | `scripts/make_tables.py` | `docs/TABLE_NUMERIC.md` |
| `num_cov` | numeric coverage | commit-safe | `docs/TABLE_NUMERIC.md` | `scripts/make_tables.py` | `docs/TABLE_NUMERIC.md` |
| `num_rel` | relative error mean | commit-safe | `docs/TABLE_NUMERIC.md` | `scripts/make_tables.py` | `docs/TABLE_NUMERIC.md` |
| `fallback_ratio` | fallback 路由比例 | local-only | `outputs/..._calc/calc_stats.json` | `scripts/run_with_calculator.py` | `outputs/<run_id>_calc/calc_stats.json` |
| `calc_used_ratio` | calculator 实际接管比例 | local-only | `outputs/..._calc/calc_stats.json` / numeric summary | `scripts/run_with_calculator.py`、`scripts/eval_numeric.py` | `outputs/<run_id>_calc/calc_stats.json` |
| `gap_vs_fallback` | calc-used 与 fallback 的 EM gap | local-only | numeric summary / `calc_stats.json` | `scripts/eval_numeric.py` | `outputs/<run_id>/summary.json` |

## C. PQE 触发字段

| 字段 | 含义 | 来源级别 | 来源文件 | 上游脚本 | 当前生成路径 / 表面 |
| --- | --- | --- | --- | --- | --- |
| `queries_expanded` | 被扩展的 query 数量 | local-only | `outputs/...m18/logs.txt`、`outputs/...m19/logs.txt` | `scripts/eval_retrieval.py` + `src/retrieval/query_expansion.py` | `outputs/<run_id>/logs.txt` |
| `prf_year_expanded_count` | 因年份 PRF 扩展的 query 数量 | local-only | 同上 | 同上 | `outputs/<run_id>/logs.txt` |
| `abbrev_expanded_count` | 因 abbrev 扩展的 query 数量 | local-only | 同上 | 同上 | `outputs/<run_id>/logs.txt` |
| `avg_num_queries` | 平均扩展后 query 数量 | local-only | 同上 | 同上 | `outputs/<run_id>/logs.txt` |

## D. Multistep 审计字段

| 字段 | 含义 | 来源级别 | 来源文件 | 上游脚本 | 当前生成路径 / 表面 |
| --- | --- | --- | --- | --- | --- |
| `stop_reasons` | multistep 终止原因分布 | local-only | `outputs/...m05_ms/logs.txt`、`...m09_ms/logs.txt`、`...m10_ms/logs.txt` | `scripts/run_multistep_retrieval.py` | `outputs/<run_id>_ms/logs.txt` |
| `MAX_STEPS` | 因达到最大步数停止 | local-only | 同上 | 同上 | 同上 |
| `GATE_BLOCKED` | 被 gap gate 阻断 | local-only | 同上 | 同上 | 同上 |
| `NO_GAP` | 无新增 gap，因此停止 | local-only | 同上 | 同上 | 同上 |

## E. comboC Supplemental 字段

| 字段 | 含义 | 来源级别 | 来源文件 | 上游脚本 | 当前生成路径 / 表面 |
| --- | --- | --- | --- | --- | --- |
| `numeric_dev.numeric_em` | comboC local mini-matrix 的 numeric EM | local-only | `outputs/20260228_012006_b44483/runs/*/summary.json` | `scripts/run_matrix_step6.py` + comboC 配置 | `outputs/20260228_012006_b44483/runs/*/summary.json` |
| `numeric_dev.coverage` | comboC local mini-matrix 的 coverage | local-only | 同上 | 同上 | 同上 |
| `used_module_counts` | combo router 中 A / B 实际使用次数 | local-only | `outputs/...m04_calc/calc_audit.json` | `scripts/run_with_calculator.py` | `outputs/..._calc/calc_audit.json` |
| `route_reason_counts` | combo router 路由原因 | local-only | 同上 | 同上 | 同上 |
| `fact_filter.kept_ratio` | fact filter 保留比例 | local-only | 同上 | 同上 | 同上 |

## F. 子集口径字段

| 字段 | 含义 | 来源级别 | 来源文件 | 上游脚本 | 当前生成路径 / 表面 |
| --- | --- | --- | --- | --- | --- |
| `complex_size` | 复杂子集样本数 | local-only | `data/subsets_v2/subsets_stats.json` | `scripts/build_subsets.py` 或相关子集构建流程 | `data/subsets_v2/subsets_stats.json` |
| `abbrev_size` | 缩写子集样本数 | local-only | 同上 | 同上 | 同上 |
| `numeric_size` | 数值子集样本数 | local-only | 同上 | 同上 | 同上 |
| `rule_hits.two_years` | 复杂子集中的双年份命中数 | local-only | 同上 | 同上 | 同上 |
| `complex_path` / `abbrev_path` / `numeric_path` | 子集文件路径 | local-only | `data/subsets_v2/subsets_stats.json`、`outputs/.../config.resolved.yaml` | 配置解析 + 评测脚本 | `data/subsets_v2/subsets_stats.json`、`outputs/<run_id>/config.resolved.yaml` |

## G. Plot Pipeline 字段

| 字段 | 含义 | 来源级别 | 来源文件 | 上游脚本 | 当前生成路径 / 表面 |
| --- | --- | --- | --- | --- | --- |
| `plot_has_data_false_count` | 启用图中无数据的数量 | commit-safe | `docs/SEAL_FINAL_CHECK.md`、`outputs/seal_checks/seal_final_snapshot.json` | `scripts/plot_all.py` + seal final check | `docs/SEAL_FINAL_CHECK.md` |
| `tables_updated` | tables 是否重生成 | commit-safe | `docs/SEAL_FINAL_CHECK.md` | seal final check | `docs/SEAL_FINAL_CHECK.md` |
| `plots_updated` | plots 是否重生成 | commit-safe | `docs/SEAL_FINAL_CHECK.md` | seal final check | `docs/SEAL_FINAL_CHECK.md` |
| `enabled_figures` | 当前启用图名称 | commit-safe | `scripts/plot_config.yaml` | `scripts/plot_all.py` | `scripts/plot_config.yaml` |

## H. 推荐的数据装配顺序

如果后续要写一个新的画图脚本，建议按以下顺序装配数据：

1. 先读取 `configs/step6_experiments_seal.yaml`，建立 `label -> run_id` 映射。
2. 从 `docs/TABLE_MAIN.md` 与 `docs/TABLE_NUMERIC.md` 读取 commit-safe 指标。
3. 仅当图需要解释性字段时，再下钻到 `outputs/**` 读取 `logs.txt`、`calc_stats.json`、`summary.json`。
4. 对任何使用 `outputs/**` 的图，都在图注中标注“local-only audit supplement”。

## I. 适合新增脚本的字段分组

- `retrieval_core`
  - `full_r10`
  - `full_mrr10`
  - `complex_r10`
  - `abbrev_r10`
- `numeric_core`
  - `num_em`
  - `num_cov`
  - `num_rel`
- `pqe_audit`
  - `queries_expanded`
  - `prf_year_expanded_count`
  - `abbrev_expanded_count`
- `multistep_audit`
  - `stop_reasons`
- `calculator_audit`
  - `fallback_ratio`
  - `calc_used_ratio`
  - `gap_vs_fallback`
- `comboc_audit`
  - `used_module_counts`
  - `route_reason_counts`
  - `fact_filter.kept_ratio`

## J. 风险提醒

- `docs/TABLE_*` 适合作为正式论文图的数据底座。
- `outputs/**` 适合作为解释图、诊断图和补充图的数据来源。
- 当前 `plot_all.py` 默认并不覆盖 PQE 触发、multistep stop reason、calculator route gap 等最重要的解释型字段，因此后续画图很可能需要新增独立脚本。
