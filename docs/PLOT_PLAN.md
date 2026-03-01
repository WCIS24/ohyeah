# Plot Plan

## 目标

本文件回答两个问题：

1. 每张图打算证明什么 claim。
2. 每张图该从哪张表、哪个字段、哪个脚本或本地审计文件取数。

图表分为两类：

- `Current seal deliverables`：已经由 `plot_all.py` 或 seal 产物生成。
- `Paper-planned figures`：更适合论文叙事，但当前未作为 seal 默认图输出。

## A. Current Seal Deliverables

| 图表编号 | 图表名称 | 状态 | 回答的 claim | 主要字段 | 数据来源 | 生成入口 | 输出路径 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | Main Results Table | 已生成 | 当前 seal 主矩阵在 Full / Complex / Abbrev 检索指标上的整体排序 | `full_r10`、`full_mrr10`、`complex_r10`、`complex_mrr10`、`abbrev_r10`、`abbrev_mrr10` | `outputs/<run_id>/summary.json`，通过 `configs/step6_experiments_seal.yaml` 汇总 | `scripts/plot_all.py` -> `main_results` | `thesis/figures_seal/ThemeA/tables/main_results.csv`、`thesis/figures_seal/ThemeA/tables/main_results.tex` |
| A2 | Ablation Breakdown | 已生成 | 消融组内部的 retrieval 指标拆解，可辅助说明 multistep / calculator / PQE ablation 的相对位置 | `full_r10`、`full_mrr10`、`complex_r10`、`complex_mrr10` | `outputs/<run_id>/summary.json` | `scripts/plot_all.py` -> `ablation_breakdown` | `thesis/figures_seal/ThemeA/figures/ablation_breakdown.pdf`、`thesis/figures_seal/ThemeA/figures/ablation_breakdown.png` |

## B. Paper-Planned Figures

| 图表编号 | 图表名称 | 回答的 claim | 建议图型 | 主要字段 | 数据来源 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | FT Gain Bar | Retriever FT 是强结论，且对 Full / Complex / Abbrev 三个口径同时有效 | 分组柱状图 | `full_r10`、`full_mrr10`、`complex_r10`、`abbrev_r10` | `docs/TABLE_MAIN.md` 中 `m01` vs `m02` | 论文主图之一 |
| B2 | Retrieval Mode Contrast | dense 是当前 seal 的唯一稳定模式，bm25 与 hybrid 都弱于 dense | 分组柱状图 | `full_r10`、`full_mrr10`、`complex_r10`、`abbrev_r10` | `docs/TABLE_MAIN.md` 中 `m02`、`m03`、`m04` | 适合放实验主结果 |
| B3 | Multistep Stop-Reason Chart | multistep 不显著不是偶然，而是大多数样本被 gate 或 `NO_GAP` 吞掉 | 堆叠条形图 | `stop_reasons` | `outputs/...m05_ms/logs.txt`、`...m09_ms/logs.txt`、`...m10_ms/logs.txt` | 本地审计补充，需标注 local-only |
| B4 | PQE Trigger and Gain | PQE 的收益主要来自 `prf_year`，而不是 abbrev-only 扩展 | 双轴图或左右并排柱图 | `queries_expanded`、`prf_year_expanded_count`、`abbrev_expanded_count`、`full_r10`、`complex_r10` | `outputs/...m18/logs.txt`、`outputs/...m19/logs.txt` + `docs/TABLE_MAIN.md` | 论文核心解释图 |
| B5 | Calculator Coverage-EM Tradeoff | calculator 当前表现为 coverage 上升、EM 下降的 tradeoff，而不是闭环增益 | 散点图或 slope chart | `num_cov`、`num_em` | `docs/TABLE_NUMERIC.md` 中 `m11`、`m12`、`m13`、`m15` | 适合放风险披露图 |
| B6 | Combination C Interaction Plot | PQE + calculator 有交互，但没有形成数值闭环 | 双指标对照图 | `num_cov`、`num_em`、`num_rel` | `docs/TABLE_NUMERIC.md` 中 `m12` vs `m20` | 论文中应配合文字强调“未闭环” |
| B7 | comboC Supplemental Audit | A-only / B-only / C-full 没有出现同时改善 EM 与 coverage 的结果，因此不是叠加幻觉 | 四组对照柱图 | `numeric_em`、`coverage` | `outputs/20260228_012006_b44483/runs/*/summary.json` + `docs/SEAL_CHECK_comboC.md` | 仅作 supplemental，需标 local-only |
| B8 | Subset Contract Audit | `subsets_v2` 已有统计定义，但 seal resolved config 仍指向旧路径 | 流程示意图或 audit 表图 | `complex_size`、`abbrev_size`、`numeric_size`、resolved subset paths | `data/subsets_v2/subsets_stats.json`、`outputs/...m18/config.resolved.yaml`、`outputs/...m20/config.resolved.yaml` | 更适合附录 |
| B9 | Reproduction Surface Diagram | 当前工程的正式证据表面是 `docs/TABLE_*` 与 `docs/SEAL_*`，不是 `outputs/` | 框图 | 命令、产物、路径 | `docs/SEAL_FREEZE_MANIFEST.md`、`docs/SEAL_FINAL_CHECK.md` | 适合方法或附录 |

## C. 图表优先级

建议按以下顺序生成论文图表：

1. `B1 FT Gain Bar`
2. `B2 Retrieval Mode Contrast`
3. `B4 PQE Trigger and Gain`
4. `B5 Calculator Coverage-EM Tradeoff`
5. `B6 Combination C Interaction Plot`
6. `B3 Multistep Stop-Reason Chart`
7. `B7 comboC Supplemental Audit`
8. `B8 Subset Contract Audit`
9. `B9 Reproduction Surface Diagram`

## D. 图表与 claim 对齐建议

- 如果正文要强调“主贡献”，优先使用 `B1`、`B2`、`B4`。
- 如果正文要强调“为何不夸大”，优先使用 `B3`、`B5`、`B6`。
- 如果答辩现场需要解释“为什么组合 C 不能写成成功”，优先使用 `B6` 与 `B7`。
- 如果答辩老师关注复现与封装，优先使用 `A1`、`A2`、`B9`。

## E. 当前图表缺口

- 当前 `plot_all.py` 只启用了 `main_results` 与 `ablation_breakdown`，因此不能直接支持论文里最关键的解释型图。
- `recall_mrr_curves`、`delta_bar`、`numeric_errors`、`multistep_trace` 在当前 seal 配置中均为 disabled。
- 若要把论文图表一次性纳入正式脚本链，需要为 `B3`、`B4`、`B5`、`B6` 新增稳定数据装配逻辑。
