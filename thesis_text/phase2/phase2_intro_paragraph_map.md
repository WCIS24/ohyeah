# 绪论段落—主张—证据映射表

| ParagraphID | What it says | Linked claim | Evidence | Risk | Later expansion (Phase 3/4/5) |
| --- | --- | --- | --- | --- | --- |
| P1 | 金融问答对证据与可追溯性要求高，复杂查询需要多步检索与数值计算 | CLM-A | 金融AI选题评价.pdf:page 1 | 背景表述过泛 | Phase 3 可补充文献综述 |
| P2 | 任务定义强调多步检索与推理整合 | CLM-A | 金融AI选题评价.pdf:page 1 | 需避免越界到方法细节 | Phase 3 补充形式化定义 |
| P3 | FinDER 数据集规模与作用 | CLM-B | 金融AI选题评价.pdf:page 1 | 数据规模引用错误风险 | Phase 4 引入数据划分说明 |
| P4 | 技术路线：baseline→multistep→calculator | CLM-D, CLM-E, CLM-F | README.md:41-131 | 与实际实现不一致 | Phase 4 结合 configs 细化 |
| P5 | 评测口径：Recall@K/MRR@K/EM/numeric_em | CLM-G | src/retrieval/eval_utils.py:38-106; scripts/eval_qa.py:120-129; scripts/eval_numeric.py:216-234 | 指标口径混用 | Phase 4 用表格规范 |
| P6 | 贡献：可复现流程 | CLM-D | README.md:41-131 | 被认为工程化 | Phase 5 讨论复现价值 |
| P7 | 贡献：模块化实现 | CLM-H | 仓库地图.pdf:page 1 | 被认为非算法贡献 | Phase 5 强调可维护性 |
| P8 | 贡献：统一评测口径 | CLM-G | src/retrieval/eval_utils.py:38-106; scripts/eval_qa.py:120-129; scripts/eval_numeric.py:216-234 | 指标实现细节不足 | Phase 4 细化评测设置 |
| P9 | 论文结构安排 | common knowledge | common knowledge | 章节安排与导师要求不一致 | Phase 3 根据要求调整 |
