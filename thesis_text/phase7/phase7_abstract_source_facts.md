# Phase 7 Abstract Source Facts

Purpose:
- 汇总摘要写作素材，确保仅来自 Phase 2/4/5/6 的既有内容。

How to use:
- 摘要写作应从下列事实中选取，不得新增实验或结论。

## Fact List
1) 背景与问题：复杂金融查询需要可追溯证据，多步检索与数值计算是核心挑战。
2) 数据集与任务：FinDER 数据集用于金融检索问答，包含 5,703 个查询-证据-答案三元组。
3) 方法概述：采用 baseline → multistep → calculator 的模块化流水线，统一数据准备、索引、评测与产物记录。
4) 评测口径：检索侧使用 Recall@K 与 MRR@K，问答侧使用 EM 与 numeric_em 等指标。
5) 核心现象：post_ft 相对 pre_ft 在 Full dev 上 Recall@10 从 0.3246 提升至 0.3789，Complex 子集亦为正增益；multistep 对 MRR@10 有轻微变化。
6) 局限与展望：单次 seed、误差分析不足、成本统计缺失，未来需补齐稳定性与错误分析。
