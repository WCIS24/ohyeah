# Phase 5 图表与表格清单

| ItemID | Type | What question it answers | Data source path(s) | Keys/fields | Intended section | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| T4-1 | Table | 主结果对比（Full/Complex 的 Recall@10/MRR@10） | thesis_text/phase5/main_results.csv; outputs/<run_id>/summary.json | metrics.retrieval_full.recall@10/mrr@10; metrics.retrieval_complex.recall@10/mrr@10 | 4.2 主结果对比 | 可同步 docs/TABLE_MAIN.md 校验 |
| T4-2 | Table | 数值 QA 表现（numeric_em / rel_error_mean / coverage） | thesis_text/phase5/main_results.csv; outputs/<run_id>/summary.json | metrics.numeric_dev.numeric_em/rel_error_mean/coverage | 4.2 主结果对比 | 仅 calculator 开启的 run 有数值指标 |
| T4-3 | Figure/Table | 相对 baseline 的 Δ 指标 | thesis_text/phase5/delta_vs_baseline.json | full_r10/full_mrr10/complex_r10/complex_mrr10 | 4.3 组件贡献 | 可用脚本自制柱状图 |
| T4-4 | Figure | Recall@K/MRR@K 曲线 | outputs/<run_id>/metrics.json | recall@k/mrr@k | 4.4 诊断分析 | 可用 scripts/plot_all.py (recall_mrr_curves) |
| T4-5 | Figure | 多步检索轨迹示例 | outputs/<run_id>_ms/multistep_traces.jsonl | trace.step_idx/gap/stop_reason | 4.5 案例研究 | 需选择代表性 qid |
| T4-6 | Table | 数值错误分布 | outputs/<run_id>_numeric/numeric_per_query.jsonl | numeric_em/abs_err/rel_err | 4.4 诊断分析 | 可统计分布后制表 |
