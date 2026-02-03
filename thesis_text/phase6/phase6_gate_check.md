# Phase 6 Gate Check

Purpose:
- 核验 Phase 5 产物是否足以支撑“结论章不引入新信息、只总结要点”的要求。

How to use:
- 若 PASS，可进入 Phase 6 写作；若 FAIL，先补齐缺失证据。

## Gate Status: PASS

## 0.1 Phase 5 核验状态
- phase5_verification_report.md 存在且 V1–V5 均为 PASS，可支撑结论中的结果性总结。[EVIDENCE] thesis_text/phase5/phase5_verification_report.md

## 0.2 可写入结论的三类要点与证据
### 研究目的 / 任务背景
- 复杂金融查询在传统 LLM 与单步检索场景下存在事实不准、跨段推理与数值计算困难，RAG 与多步检索/数值推理是核心挑战与动机。[EVIDENCE] my-thesis/金融AI选题评价.pdf:page 1
- FinDER 数据集用于刻画金融领域复杂查询与证据需求，体现跨段检索与数值推理场景。[EVIDENCE] my-thesis/金融AI选题评价.pdf:page 1

### 方法贡献点（与 Phase 1 对齐）
- 构建 baseline → multistep → calculator 的模块化流水线，明确数据处理、检索、评测与产物契约，支撑可复现实验。[EVIDENCE] README.md:41-131; thesis_text/phase4/ch03_method_v1.md
- 多步检索与计算器模块已有可复述设计文档，并与代码实现一一对应。[EVIDENCE] docs/multistep_design.md; docs/calculator_design.md; thesis_text/phase4/ch03_method_v1.md
- 评测口径与指标实现明确（Recall@K / MRR@K / numeric_em 等），可作为结论中的评价基准。[EVIDENCE] src/retrieval/eval_utils.py:38-107; scripts/eval_numeric.py:151-234; thesis_text/phase4/ch03_method_v1.md

### 实验核心结果现象
- post_ft 相对 pre_ft 在 Full/Complex 上 Recall@10 与 MRR@10 均为正增量。[EVIDENCE] thesis_text/phase5/delta_vs_baseline.json; thesis_text/phase5/main_results.csv
- multistep 在 post_ft 下保持 Recall@10 不变而 MRR@10 轻微变化。[EVIDENCE] thesis_text/phase5/main_results.csv; thesis_text/phase5/ch04_experiments_v1.md
- calculator 开启后产生 numeric_em/coverage 等数值指标，且检索指标与对应 baseline 一致。[EVIDENCE] thesis_text/phase5/main_results.csv; thesis_text/phase5/ch04_experiments_v1.md

## 0.3 缺失项检查
- 无（当前证据足以支持结论章不引入新信息的写作要求）。
