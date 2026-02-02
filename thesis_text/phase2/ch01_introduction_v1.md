第一章 绪论

1.1 研究背景与动机
金融领域问答需要以可追溯的证据为基础来保证回答的可靠性，而检索增强生成（RAG）为此提供了“先检索后生成”的基本范式。复杂金融查询往往涉及跨文档或跨段落的信息组合，传统单步检索在此类问题上容易遗漏关键证据。为应对多跳检索与数值计算需求，本研究以多步检索与显式计算为核心动机展开系统化探索。[EVIDENCE] 金融AI选题评价.pdf:page 1

1.2 问题定义与任务边界
本文聚焦复杂金融查询的检索问答任务：给定金融领域查询与语料库，系统需要检索证据并给出可验证的答案，必要时执行数值计算。该定义强调多步检索与推理整合，是本文的任务边界与评测语境。[EVIDENCE] 金融AI选题评价.pdf:page 1
FinDER 数据集由金融领域专家构建，包含 5,703 个查询-证据-答案三元组，是本文实验的主要数据基础与问题载体。[EVIDENCE] 金融AI选题评价.pdf:page 1

1.3 技术路线概述
本文采用 baseline → multistep retrieval → calculator 的模块化流水线，从数据准备、检索评估、单步基线到多步检索与数值计算逐步展开，形成可复现的实验链路。[EVIDENCE] README.md:41-131
评测口径覆盖检索与问答两个层面：检索侧使用 Recall@K 与 MRR@K，问答侧使用 Exact Match/EM 与数值评测指标 numeric_em 及误差统计，以保证对检索与数值推理能力的可比性描述。[EVIDENCE] src/retrieval/eval_utils.py:38-106; scripts/eval_qa.py:120-129; scripts/eval_numeric.py:216-234

1.4 主要贡献
第一，提供覆盖 baseline、多步检索与数值计算的可复现流程骨架，并以配置驱动的脚本组织实验步骤，便于后续复现实验与扩展比较。[EVIDENCE] README.md:41-131
第二，系统实现采用 data/indexing/retrieval/multistep/calculator 的模块化结构，便于清晰描述与分模块验证实验设置。[EVIDENCE] 仓库地图.pdf:page 1
第三，明确检索、QA 与数值 QA 的指标口径与实现，支撑论文实验部分的统一表述与对比。[EVIDENCE] src/retrieval/eval_utils.py:38-106; scripts/eval_qa.py:120-129; scripts/eval_numeric.py:216-234

1.5 论文结构安排
第二章将综述相关工作并界定本文与既有研究的关系；第三章描述方法框架与关键模块；第四章说明实验设置与评测口径；第五章报告实验结果并进行分析；第六章讨论局限性与可能改进；第七章给出总结与展望。[EVIDENCE] common knowledge
