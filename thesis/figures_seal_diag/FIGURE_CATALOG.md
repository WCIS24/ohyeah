# FIGURE_CATALOG

## 主结果总表
- 问题：不同方法在 Full/Complex 检索指标上的整体对比表现。
- 数据源：
  - configs/step6_experiments_seal.yaml (run_id 列表)
  - outputs/<run_id>/summary.json
- 生成脚本入口：`scripts/plot_all.py (main_results)`
- 输出文件：
  - thesis/figures_seal_diag/ThemeA/tables/main_results.csv
  - thesis/figures_seal_diag/ThemeA/tables/main_results.tex
- LaTeX 引用：

```
\begin{table}[t]
\centering
\caption{TODO: 主结果对比（生成日期 2026-02-18）}
\label{tab:main_results}
\input{thesis/figures_seal_diag/ThemeA/tables/main_results.tex}
\end{table}
```

- 状态：ok

## Recall@k / MRR@k 曲线
- 问题：不同方法随 k 变化的检索召回与排序质量。
- 数据源：
  - outputs/<run_id>/metrics.json
- 生成脚本入口：`scripts/plot_all.py (recall_mrr_curves)`
- 输出文件：
  - thesis/figures_seal_diag/ThemeA/figures/recall_mrr_k.pdf
  - thesis/figures_seal_diag/ThemeA/figures/recall_mrr_k.png
- LaTeX 引用：

```
\begin{figure}[t]
\centering
\includegraphics[width=0.95\linewidth]{thesis/figures_seal_diag/ThemeA/figures/recall_mrr_k.pdf}
\caption{TODO: Recall@k 与 MRR@k 随 k 变化曲线}
\label{fig:recall_mrr_k}
\end{figure}
```

- 状态：TODO: missing metrics.json

## 相对 Baseline 的 Δ 指标
- 问题：方法相对 baseline 的提升幅度（Δ 形式）。
- 数据源：
  - outputs/<run_id>/(delta_vs_baseline.json | delta_vs_pre.json)
- 生成脚本入口：`scripts/plot_all.py (delta_bar)`
- 输出文件：
  - thesis/figures_seal_diag/ThemeA/figures/delta_bar.pdf
  - thesis/figures_seal_diag/ThemeA/figures/delta_bar.png
- LaTeX 引用：

```
\begin{figure}[t]
\centering
\includegraphics[width=0.85\linewidth]{thesis/figures_seal_diag/ThemeA/figures/delta_bar.pdf}
\caption{TODO: 相对 baseline 的指标提升}
\label{fig:delta_bar}
\end{figure}
```

- 状态：TODO: missing delta_vs_baseline.json

## 消融拆解图
- 问题：从 baseline → multistep → +calculator 的分步贡献。
- 数据源：
  - outputs/<run_id>/summary.json
- 生成脚本入口：`scripts/plot_all.py (ablation_breakdown)`
- 输出文件：
  - thesis/figures_seal_diag/ThemeA/figures/ablation_breakdown.pdf
  - thesis/figures_seal_diag/ThemeA/figures/ablation_breakdown.png
- LaTeX 引用：

```
\begin{figure}[t]
\centering
\includegraphics[width=0.85\linewidth]{thesis/figures_seal_diag/ThemeA/figures/ablation_breakdown.pdf}
\caption{TODO: 消融拆解对比}
\label{fig:ablation_breakdown}
\end{figure}
```

- 状态：ok

## Abbrev subset breakdown
- 问题：How do runs perform on abbreviation-heavy subset retrieval?
- 数据源：
  - outputs/<run_id>/summary.json
- 生成脚本入口：`scripts/plot_all.py (abbrev_breakdown)`
- 输出文件：
  - thesis/figures_seal_diag/ThemeA/figures/abbrev_breakdown.pdf
  - thesis/figures_seal_diag/ThemeA/figures/abbrev_breakdown.png
- LaTeX 引用：

```
\begin{figure}[t]
\centering
\includegraphics[width=0.85\linewidth]{thesis/figures_seal_diag/ThemeA/figures/abbrev_breakdown.pdf}
\caption{TODO: Abbrev subset retrieval comparison}
\label{fig:abbrev_breakdown}
\end{figure}
```

- 状态：ok

## 数值 QA 误差分布
- 问题：数值计算模块的误差分布与稳定性。
- 数据源：
  - outputs/<run_id>/numeric_per_query.jsonl
- 生成脚本入口：`scripts/plot_all.py (numeric_errors)`
- 输出文件：
  - thesis/figures_seal_diag/ThemeA/figures/numeric_error_dist.pdf
  - thesis/figures_seal_diag/ThemeA/figures/numeric_error_dist.png
- LaTeX 引用：

```
\begin{figure}[t]
\centering
\includegraphics[width=0.85\linewidth]{thesis/figures_seal_diag/ThemeA/figures/numeric_error_dist.pdf}
\caption{TODO: 数值 QA 误差分布}
\label{fig:numeric_error_dist}
\end{figure}
```

- 状态：TODO: missing numeric_per_query.jsonl

## 多步检索轨迹案例
- 问题：展示多步检索在单样本上的步骤与收集证据变化。
- 数据源：
  - outputs/<run_id>/multistep_traces.jsonl
- 生成脚本入口：`scripts/plot_all.py (multistep_trace)`
- 输出文件：
  - thesis/figures_seal_diag/ThemeA/figures/multistep_trace_case.pdf
  - thesis/figures_seal_diag/ThemeA/figures/multistep_trace_case.png
- LaTeX 引用：

```
\begin{figure}[t]
\centering
\includegraphics[width=0.95\linewidth]{thesis/figures_seal_diag/ThemeA/figures/multistep_trace_case.pdf}
\caption{TODO: 多步检索轨迹案例}
\label{fig:multistep_trace_case}
\end{figure}
```

- 状态：TODO: missing multistep_traces.jsonl

