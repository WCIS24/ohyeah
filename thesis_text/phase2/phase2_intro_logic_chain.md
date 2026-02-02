# 绪论逻辑链（Phase 2）

Purpose:
- 明确绪论从背景到任务定义再到技术路线与贡献的逻辑承接，用于后续段落扩展与核验。

How to use:
- 每条链路对应绪论中的一个段落或小节；写作时按链路顺序展开。

1) 背景：金融问答需要可追溯证据 → RAG 提供“先检索后生成”的基本范式。[EVIDENCE] 金融AI选题评价.pdf:page 1
2) 痛点：复杂金融查询涉及跨段落/跨文档信息与数值计算，单步检索可能遗漏关键证据。[EVIDENCE] 金融AI选题评价.pdf:page 1
3) 任务定义：面向复杂金融查询的检索问答，强调 multi-hop 检索与必要时的数值计算。[EVIDENCE] 金融AI选题评价.pdf:page 1
4) 数据支撑：FinDER 数据集（查询-证据-答案三元组）作为任务载体与实验基础。[EVIDENCE] 金融AI选题评价.pdf:page 1
5) 技术路线：baseline → multistep → calculator 的模块化流水线，形成可复现实验链路。[EVIDENCE] README.md:41-131
6) 评测口径：检索侧 Recall@K/MRR@K，问答侧 EM 与 numeric_em 等，保证可比性描述。[EVIDENCE] src/retrieval/eval_utils.py:38-106; scripts/eval_qa.py:120-129; scripts/eval_numeric.py:216-234
7) 贡献落位：可复现流程、模块化实现与统一评测口径（不预设性能领先）。[EVIDENCE] README.md:41-131; 仓库地图.pdf:page 1
8) 结构安排：后续章节按“方法—实验—结果—讨论—结论”展开。[EVIDENCE] common knowledge
