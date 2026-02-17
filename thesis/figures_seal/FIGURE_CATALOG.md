# FIGURE_CATALOG

## 主结果总表
- 问题：不同方法在 Full/Complex 检索指标上的整体对比表现。
- 数据源：
  - configs/step6_experiments_seal.yaml (run_id 列表)
  - outputs/<run_id>/summary.json
- 生成脚本入口：`scripts/plot_all.py (main_results)`
- 输出文件：
  - thesis/figures_seal/ThemeA/tables/main_results.csv
  - thesis/figures_seal/ThemeA/tables/main_results.tex
- LaTeX 引用：

```
\begin{table}[t]
\centering
\caption{TODO: 主结果对比（生成日期 2026-02-17）}
\label{tab:main_results}
\input{thesis/figures_seal/ThemeA/tables/main_results.tex}
\end{table}
```

- 状态：ok

## Abbrev subset breakdown
- 问题：How do runs perform on abbreviation-heavy subset retrieval?
- 数据源：
  - outputs/<run_id>/summary.json
- 生成脚本入口：`scripts/plot_all.py (abbrev_breakdown)`
- 输出文件：
  - thesis/figures_seal/ThemeA/figures/abbrev_breakdown.pdf
  - thesis/figures_seal/ThemeA/figures/abbrev_breakdown.png
- LaTeX 引用：

```
\begin{figure}[t]
\centering
\includegraphics[width=0.85\linewidth]{thesis/figures_seal/ThemeA/figures/abbrev_breakdown.pdf}
\caption{TODO: Abbrev subset retrieval comparison}
\label{fig:abbrev_breakdown}
\end{figure}
```

- 状态：ok

