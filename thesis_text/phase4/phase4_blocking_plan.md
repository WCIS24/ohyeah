# Phase 4 阻塞项处理计划表

Purpose:
- 将 Top 5 阻塞项转为可执行计划，并明确证据来源与预期产物。

How to use:
- 按表格逐条执行，完成后在 changelog 与 verification 报告中标记状态。

| TODO | Target artifact | Where to get evidence | Action plan | Expected files | Status |
| --- | --- | --- | --- | --- | --- |
| (1) 数据集切分规模（train/dev/test 计数） | docs/data_stats.json | outputs/<run_id>/data_stats.json; outputs/<run_id>/subsets_stats.json | 运行 prepare_data + build_subsets 生成统计；新增 scripts/compute_data_stats.py 合并并落盘 docs/data_stats.json | docs/data_stats.json; scripts/compute_data_stats.py; configs/data_stats.yaml; outputs/<run_id>/metrics.json | DONE |
| (2) 多步检索 Planner/Gap/Stop/Refiner 细节 | docs/multistep_design.md | src/multistep/{planner,gap,stop,refiner}.py; src/multistep/engine.py | 补充 docstring/注释并编写设计说明文档；更新方法章 3.4 引用 | docs/multistep_design.md; ch03_method_v1.md | DONE |
| (3) 计算器任务类型与规则库说明 | docs/calculator_design.md | src/calculator/{extract,compute}.py; scripts/run_with_calculator.py; scripts/eval_numeric.py | 编写规则/触发逻辑与任务类型说明文档；更新方法章 3.6 引用 | docs/calculator_design.md; ch03_method_v1.md | DONE |
| (4) baseline 生成模块是否需要真实 LLM | docs/repro_env_and_llm_dependency.md | scripts/run_baseline.py; README.md | 明确 baseline 为模板式生成，无外部 LLM 依赖；给出 retrieval-only/full QA 最短命令 | docs/repro_env_and_llm_dependency.md; ch03_method_v1.md | DONE |
| (5) 关键 run_id 与主结果表可引用路径核对 | thesis_text/phase_fix/outputs_index.md | outputs/<run_id>/metrics.json; configs/step6_experiments.yaml; thesis/figures/FIGURE_CATALOG.md | 更新 outputs_index：补充 data_stats/run_ids；列出 step6 表格所需 run_id 与缺失状态 | thesis_text/phase_fix/outputs_index.md | DONE |
