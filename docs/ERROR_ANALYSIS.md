# 错误分析与案例

本节基于 Step6 的 `error_buckets.py` 统计结果与 multistep traces，给出主要失败类型与典型案例。所有数值均可在 `outputs/<run_id>/error_bucket_stats.json`、`outputs/<run_id>/multistep_traces.jsonl` 中复现。

## 1) 失败类型概览（自动统计）

以下为 Step6 六组矩阵实验的自动统计摘要：

- Run 20260130_234540_ae7cdf_m01: numeric_buckets={'fallback': 570}
- Run 20260130_234540_ae7cdf_m02: numeric_buckets={'fallback': 570}
- Run 20260130_234540_ae7cdf_m03: complex_buckets={'max_steps': 45, 'no_gap': 525}
- Run 20260130_234540_ae7cdf_m04: numeric_buckets={'fallback': 570}
- Run 20260130_234540_ae7cdf_m05: numeric_buckets={'fallback': 570}; complex_buckets={'max_steps': 45, 'no_gap': 525}
- Run 20260130_234540_ae7cdf_m06: numeric_buckets={'fallback': 570}; complex_buckets={'max_steps': 46, 'no_gap': 524}

解释：
- **numeric_buckets=fallback**：由于 Step6 最优门控将 `allow_task_types=[]`，计算器任务被完全关闭，所有样本都回退到 baseline；因此 numeric 失败类型呈现为 fallback。
- **complex_buckets=no_gap / max_steps**：多步检索在大部分样本中检测到 gap 并运行至 max_steps；在未发现 gap 的样本中直接停止（no_gap）。

## 2) 典型复杂查询案例（complex_dev）

**qid**: `8c8c8c34`

**query**: 
> Hasbro (HAS) 2023 one-time charges impact on operating profitability vs historical trends and cap allocation implications.

**多步检索轨迹摘要**（来自 `outputs/20260130_234540_ae7cdf_m03_ms/multistep_traces.jsonl`）：
- step0: gap=MISSING_ENTITY, gap_conf=1.0, gate_decision=true, stop_reason=CONTINUE
- step1: gap=MISSING_ENTITY, gap_conf=1.0, stop_reason=MAX_STEPS
- final_topk_size=10

**候选证据（部分 chunk_id）**：
- 008beea7_e0_c0
- 8c8c8c34_e0_c2
- f8aec91a_e0_c1
- 8caea930_e0_c2
- caa865da_e0_c3

**分析**：
该问题涉及“对比历史趋势 + 一次性费用影响”，属于复杂查询。多步检索识别到 entity/compare 型 gap，但 refined query 与原查询高度相似，导致第二步检索未引入新证据（newly_added_chunk_ids 为空），最终以 MAX_STEPS 停止。该案例反映出 **refiner 仍偏保守**，需要进一步提升 entity 拆分与精细化 query 改写能力。

## 3) 数值题失败模式（numeric_dev）

当前版本中计算器通过门控被关闭（allow_task_types=[]），所有数值题回退到 baseline，从而避免 Numeric-EM 下降，但也导致 **计算器未体现增益**。后续工作需结合更可靠的单位/年份对齐与置信度校准，逐步解除 gate 并验证 Numeric-EM/RelErr 的提升。
