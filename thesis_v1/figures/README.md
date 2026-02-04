# FIGURES README

日期：2026-02-01

## Step 2 — 结果数据扫描与作图范围
- 仓库内未发现 `outputs/` 目录，也未发现 `docs/RESULTS*.md`、`docs/FIGURES*.md`、
  `TABLE_*.md` 等结果汇总文件。
- 发现 `configs/step6_experiments.yaml`，列出了可用于绘图的 run_id（需要对应的
  `outputs/<run_id>/` 目录存在）。
- 代码层面可用的结果文件形态（当 outputs 存在时）：
  - `outputs/<run_id>/summary.json`（`scripts/run_experiment.py` 聚合结果）
  - `outputs/<run_id>/metrics.json`（检索 Recall/MRR 曲线）
  - `outputs/<run_id>/numeric_metrics.json`、`numeric_per_query.jsonl`（数值 QA 误差）
  - `outputs/<run_id>/delta_vs_baseline.json` / `delta_vs_pre.json`（Δ 指标）
  - `outputs/<run_id>/multistep_traces.jsonl`（多步检索轨迹）
- 因当前缺少真实 outputs，绘图脚本会跳过对应图表并在 FIGURE_CATALOG 标记 TODO。

## Step 3 — 配色方案定位
- 未在仓库中发现既有 `palettes.yaml` / `*.mplstyle` / `STYLE_GUIDE.md`。
- 已新增默认主题文件：`thesis/figures/style/palettes.yaml`（ThemeA/B/C）。
  若你提供新 palette 文件，可直接替换该文件。

## Step 4 — 角色编码表
- 已新增 `thesis/figures/style/role_map.yaml`，统一定义角色 → 颜色键/线型/marker。
- 包含对 `step6_experiments.yaml` 的常见标签别名映射，确保角色一致。
- 所有图表均通过 role_map 读取样式，禁止在代码中 hardcode。

## 计划生成的图表（数据就绪后）
- 主结果总表（LaTeX + CSV）
- Recall@k / MRR@k 曲线
- 相对 baseline 的 Δ 指标条形图
- 消融拆解图（分组条形）
- 数值 QA 误差分布（可选）
- 多步检索轨迹案例图（可选）
