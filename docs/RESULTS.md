# 实验结果

本节直接引用 Step6 自动生成的结果表与指标文件（见 `docs/TABLE_MAIN.md`、`docs/TABLE_NUMERIC.md`），并给出关键对照结论。对应 run_id 见 `configs/step6_experiments.yaml`。

## 1) 检索效果（full dev / complex dev）

主表见：`docs/TABLE_MAIN.md`

关键结论（complex dev）：
- **baseline(post-ft) vs best multistep**
  - Recall@10：0.3909465 → 0.3909465（持平）
  - MRR@10：0.2960138 → 0.2960873（+0.00007）

retriever 微调带来的整体提升（full dev）：
- pre-ft baseline → post-ft baseline：Recall@10 从 0.3246 提升到 0.3772（+0.0526）

## 2) 数值题表现（numeric dev）

数值表见：`docs/TABLE_NUMERIC.md`

关键对照（numeric dev）：
- **baseline(post-ft) vs best calc gate**
  - Numeric-EM：0.3838 → 0.3838（持平）
  - RelErr(mean)：683.3536 → 683.3536（持平）
  - Coverage：0.6266 → 0.6266（持平）

说明：当前版本计算器门控在 dev 上选择 `allow_task_types=[]`，以避免数值误差回退。因此 numeric 指标未出现回退，但也尚未体现提升。该结果为“安全启用”基线，可在后续提升抽取/计算置信度后再重新开启任务类型。

## 3) 六组矩阵实验（Step6）
run_id 对照：
- pre_ft_baseline: `20260130_234540_ae7cdf_m01`
- post_ft_baseline: `20260130_234540_ae7cdf_m02`
- post_ft_multistep_best: `20260130_234540_ae7cdf_m03`
- post_ft_baseline_calc_best: `20260130_234540_ae7cdf_m04`
- post_ft_multistep_calc_best: `20260130_234540_ae7cdf_m05`
- post_ft_multistep_T1_calc_best: `20260130_234540_ae7cdf_m06`

详细指标已自动写入对应的 `outputs/<run_id>/summary.json` 与 `docs/TABLE_*.md`。
