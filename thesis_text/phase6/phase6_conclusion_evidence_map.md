# Phase 6 Conclusion Evidence Map

Purpose:
- 将结论章每段/每条贡献与其证据来源逐一绑定，确保不引入新信息。

How to use:
- 若结论内容修改，需同步更新对应条目证据。

| ItemID | What it says | Evidence |
| --- | --- | --- |
| P1 | 复杂金融查询动机、RAG 与多步/数值需求；围绕 FinDER 构建可复现流水线并统一产物（含 run_id/outputs 证据链） | my-thesis/金融AI选题评价.pdf:page 1; README.md:41-131; README.md:26-29; thesis_text/phase4/ch03_method_v1.md |
| P2 | post_ft 相对 pre_ft 的 Recall@10/MRR@10 提升；multistep 对 MRR 有轻微变化；calculator 产生 numeric_em/coverage 且检索指标一致 | thesis_text/phase5/main_results.csv; thesis_text/phase5/ch04_experiments_v1.md; outputs/20260130_014940_21aa62_m01/summary.json; outputs/20260130_014940_21aa62_m02/summary.json; outputs/20260130_014940_21aa62_m04/summary.json |
| P3-1 | 数据准备与索引构建流程与数据统计可引用 | configs/prepare_data.yaml; scripts/prepare_data.py:64-145; docs/data_stats.json |
| P3-2 | baseline → multistep → calculator 的模块化流水线与产物契约 | README.md:41-131; thesis_text/phase4/ch03_method_v1.md |
| P3-3 | 多步检索与计算器设计文档与代码对应 | docs/multistep_design.md; docs/calculator_design.md; src/multistep/engine.py; src/calculator/compute.py |
| P3-4 | 评测口径与指标实现可追溯 | src/retrieval/eval_utils.py:38-107; scripts/eval_numeric.py:151-234 |
| P4 | 单次 seed、误差分析不足、成本统计缺失与生成端策略的局限 | thesis_text/phase5/ch04_experiments_v1.md; thesis_text/phase5/phase5_blocking_todos_top5.md; docs/repro_env_and_llm_dependency.md |
