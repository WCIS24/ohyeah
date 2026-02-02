# Phase 2 阻塞项 Top 5

Purpose:
- 列出仍会阻塞绪论深化与后续章节写作的关键缺口。

How to use:
- 逐条补齐对应证据或外部文献后再进入更深层写作。

| Blocking item | Why it blocks | Minimal fix | Evidence |
| --- | --- | --- | --- |
| 相关工作外部文献缺失 | 绪论与相关工作需建立学术语境 | 提供文献标题或 BibTeX 列表（不少于 15 篇） | [EVIDENCE] TODO |
| 主结果汇总表缺失（summary.json） | 后续章节需要结果表支撑 | 生成 outputs/<run_id>/summary.json 并更新表格 | [EVIDENCE] thesis/figures/FIGURE_CATALOG.md:3-24 |
| main_results.csv 为空 | 结果章节无法引用主表 | 运行 make_tables 并补齐 run_id 输出 | [EVIDENCE] thesis/figures/ThemeA/tables/main_results.csv:1-7 |
| 复杂子集与数值子集解释性不足 | 绪论只能描述任务背景，实验设置需补充定义 | 在实验设置章节详细引用 configs/build_subsets.yaml 与 configs/eval_numeric.yaml | [EVIDENCE] configs/build_subsets.yaml:1-15; configs/eval_numeric.yaml:1-6 |
| 论文结构与导师要求未确认 | 结构安排可能需调整 | 提供导师要求或学院模板 | [EVIDENCE] TODO |
