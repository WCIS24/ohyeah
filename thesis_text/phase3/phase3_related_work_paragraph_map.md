# 相关工作段落—论点—引用映射表

| ParagraphID | What it argues | Needed citations (placeholders) | Relation to our work | Risk if uncited | TODO to resolve |
| --- | --- | --- | --- | --- | --- |
| RW-2.1-1 | RAG 是证据可追溯的常见范式 | [CITE:TODO-rag-survey-2023] | 提供背景语境 | 背景无权威来源 | 补齐 RAG 综述/代表性论文 |
| RW-2.1-2 | 金融 QA 与事实核验强调证据链 | [CITE:TODO-financial-qa-2023] | 强化任务场景 | 论断泛化 | 补齐金融 QA 代表性工作 |
| RW-2.1-3 | 金融场景要求更高可解释性 | [CITE:TODO-financial-fact-verification-2024] | 说明定位动机 | 论断无证据 | 补齐金融事实核验论文 |
| RW-2.2-1 | 多跳检索以分步检索补全证据链 | [CITE:TODO-multihop-retrieval-2022] | 说明多步检索动机 | 多跳检索来源不明 | 补齐多跳检索论文 |
| RW-2.2-2 | 查询改写/迭代检索是常见策略 | [CITE:TODO-query-reformulation-2023] | 说明策略类别 | 方法类型不清 | 补齐查询改写论文 |
| RW-2.2-3 | 多步检索需关注评测口径一致性 | [CITE:TODO-iterative-retrieval-2024] | 为口径风险铺垫 | 口径讨论缺引用 | 补齐口径讨论文献 |
| RW-2.3-1 | 工具增强方法用于可控推理 | [CITE:TODO-tool-augmented-rag-2023] | 说明工具增强动机 | 工具增强泛化 | 补齐工具增强代表作 |
| RW-2.3-2 | 数值推理关注数值抽取与计算 | [CITE:TODO-numeric-reasoning-2022] | 说明数值推理需求 | 论断缺支撑 | 补齐数值推理论文 |
| RW-2.3-3 | 计算器降低算术错误风险 | [CITE:TODO-calculator-qa-2024] | 与本文 calculator 对齐 | 结论缺证据 | 补齐 calculator QA 论文 |
| RW-2.4-1 | FinDER 数据集作为研究载体 | [EVIDENCE] 金融AI选题评价.pdf:page 1 | 确立数据基础 | 数据集来源不明 | 已有证据 |
| RW-2.4-2 | 指标口径：Recall@K/MRR@K/EM/numeric_em | [EVIDENCE] src/retrieval/eval_utils.py:38-106; scripts/eval_qa.py:120-129; scripts/eval_numeric.py:216-234 | 统一评测口径 | 指标定义混用 | 已有证据 |
| RW-2.4-3 | 多步检索需对齐 top_k 与 k_values | [EVIDENCE] README.md:114-116; outputs/20260202_141735_63db48/candidate_count_summary.json | 保障公平性 | 口径风险 | 已有证据 |
| RW-2.5-1 | 本工作流水线定位与不预设性能领先 | [EVIDENCE] README.md:41-131 | 定位陈述 | 被质疑空泛 | 已有证据 |
| RW-2.5-2 | 与多步检索/工具增强交叉定位 | [EVIDENCE] 仓库地图.pdf:page 1; thesis_text/phase1/phase1_contribution_statements.md | 定位与贡献对齐 | 贡献夸大风险 | 已有证据 |
