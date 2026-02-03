# Phase 6 Conclusion Outline

Purpose:
- 规划结论章结构与证据指针，确保不引入新信息。

How to use:
- 先对照每段证据指针，再写正文；严格避免“禁止内容”。

## 5.1 研究工作总结（目的 → 方法 → 结果）
- 要写什么：
  - 回扣复杂金融查询的动机与任务范围（RAG、多步检索、数值计算需求）。
  - 概述本文的模块化方案（baseline → multistep → calculator），强调可复现与证据链。
  - 概括核心实验现象（post_ft 优于 pre_ft；multistep 影响 MRR；calculator 产生 numeric 指标）。
- 证据指针：
  - my-thesis/金融AI选题评价.pdf:page 1
  - README.md:41-131
  - thesis_text/phase4/ch03_method_v1.md
  - thesis_text/phase5/main_results.csv
  - thesis_text/phase5/delta_vs_baseline.json
- 禁止出现：
  - 未在 Phase 5 中出现的新实验/新指标/新数据
  - SOTA/显著性等无法证明的表述

## 5.2 主要贡献（3–5 条，克制表述）
- 要写什么：
  - 数据准备与索引构建的统一流程与数据统计证据。
  - baseline → multistep → calculator 的模块化流水线与产物契约。
  - 多步检索与计算器设计文档对齐实现，便于复现与解释。
  - 评测口径与指标实现清晰，实验结果可追溯。
- 证据指针：
  - configs/prepare_data.yaml; scripts/prepare_data.py
  - docs/data_stats.json; outputs/20260202_165254_c4b131/data_stats.json
  - README.md:41-131
  - docs/multistep_design.md; docs/calculator_design.md
  - src/retrieval/eval_utils.py:38-107; scripts/eval_numeric.py:151-234
- 禁止出现：
  - “首次/开创/领先”等无法证实措辞
  - 未在 Phase 4/5 文档中出现的功能/模块

## 5.3 局限性与未来工作
- 要写什么：
  - 单次 seed、缺乏方差/置信区间等稳定性限制。
  - 误差分析与数值错误分布未系统统计。
  - 资源/成本统计不足与更强生成器的潜在空间（不引入新方法）。
- 证据指针：
  - thesis_text/phase5/ch04_experiments_v1.md (4.6 小结与局限)
  - thesis_text/phase5/phase5_blocking_todos_top5.md
  - docs/repro_env_and_llm_dependency.md
- 禁止出现：
  - TODO/占位符
  - 未在 Phase 5 明确的新增对比实验计划
