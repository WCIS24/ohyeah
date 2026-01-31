# 实验结果与分析

本节直接引用 Step6 输出的表格与指标（见 `docs/TABLE_MAIN.md`、`docs/TABLE_NUMERIC.md`），并对主要对照结果进行分析。

## 1) 检索效果（full dev / complex dev）

**主结果表见**：`docs/TABLE_MAIN.md`

关键对照（complex dev）：
- baseline(post-ft) vs best multistep：
  - Recall@10：0.3909465 → 0.3909465（持平）
  - MRR@10：0.2960138 → 0.2960873（+0.00007）

检索器微调带来的整体提升（full dev）：
- pre-ft baseline → post-ft baseline：Recall@10 0.3246 → 0.3772（+0.0526）

## 2) 数值题表现（numeric dev）

**数值表见**：`docs/TABLE_NUMERIC.md`

关键对照（numeric dev）：
- baseline(post-ft) vs best calc gate：
  - Numeric-EM：0.3838 → 0.3838（持平）
  - RelErr(mean)：683.3536 → 683.3536（持平）
  - Coverage：0.6266 → 0.6266（持平）

说明：当前版本计算器门控在 dev 上选择 allow\_task\_types=[]，以避免数值误差回退。因此 numeric 指标未下降，但尚未体现提升。该结果为“安全启用”基线，可在后续提升抽取/计算置信度后再重新开启任务类型。

## 3) 消融与案例

- 消融结果见 `docs/TABLE_ABLATION.md`
- 典型复杂查询案例见附录 B（3 个案例，包含多步检索每步 top-3 证据与 stop 原因）
