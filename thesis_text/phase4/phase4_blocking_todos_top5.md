# 方法章阻塞项 Top 5

Purpose:
- 仅列出会阻塞 Phase 5 实验写作或方法可复现性的缺口，并给出最小补齐路径。

How to use:
- 逐条补齐后在 Phase 5 中引用相应证据文件。

| Missing item | Why needed | Where to find (expected file/command) | How to obtain | Owner |
| --- | --- | --- | --- | --- |
| 数据集切分规模（train/dev/test 计数） | 实验章需要报告数据规模与划分 | outputs/<run_id>/data_stats.json | 运行 `python scripts\prepare_data.py --config configs\prepare_data.yaml` 并保存 outputs/<run_id>/data_stats.json | user |
| 多步检索的 Planner/Gap/Stop/Refiner 细节 | 方法章需更细的算法描述与止损逻辑 | src/multistep/planner.py; src/multistep/gap.py; src/multistep/stop.py; src/multistep/refiner.py | 阅读并提炼关键规则，补写到方法章 3.4 | user |
| 计算器任务类型与规则库说明 | 解释 numeric 任务与 gate 规则来源 | src/calculator/compute.py | 阅读 compute_for_query 与任务类型定义，补写到方法章 3.6 | user |
| Baseline 生成模块是否需要真实 LLM | 若论文定位为 RAG 系统，需明确生成模块实现边界 | scripts/run_baseline.py | 选择：保持模板生成并在论文注明，或实现 LLM 生成并更新脚本 | user |
| 关键 run_id 与主结果表的可引用路径 | Phase 5 需要对齐 metrics.json 与表格汇总 | thesis_text/phase_fix/outputs_index.md; outputs/<run_id>/metrics.json | 确认 outputs_index 中的 run_id 与配置一致，必要时补跑 | user |
