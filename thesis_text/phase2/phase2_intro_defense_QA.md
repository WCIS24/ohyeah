# 绪论答辩/审稿追问预案

1) 为什么选择 FinDER 作为主要数据集？
- 回答：FinDER 是金融领域专家构建的检索问答数据集，包含查询-证据-答案三元组，契合本文任务定义。[EVIDENCE] 金融AI选题评价.pdf:page 1

2) 复杂金融查询的挑战在哪里？
- 回答：复杂查询需要跨段落检索与数值计算，多步检索与推理整合是关键挑战。[EVIDENCE] 金融AI选题评价.pdf:page 1

3) 为什么需要多步检索而不是单步检索？
- 回答：任务定义强调 multi-hop retrieval 场景，单步检索可能无法覆盖分散证据；本文以多步检索作为方法动机。[EVIDENCE] 金融AI选题评价.pdf:page 1

4) 评测口径是否一致且可复现？
- 回答：检索与问答评测口径由脚本实现并输出，包含 recall@k、mrr@k、exact_match 与 numeric_em 等指标，且落盘于 outputs/<run_id>/metrics.json 或 numeric_metrics.json。[EVIDENCE] src/retrieval/eval_utils.py:38-106; scripts/eval_qa.py:120-129; scripts/eval_numeric.py:216-234; 仓库地图.pdf:page 1

5) baseline 与 multistep 的比较是否公平？
- 回答：需要保证 top_k_final 与评测 k_values 对齐；本文在方法与实验设置中将明确该约束，并通过候选数统计报告核验是否存在截断。[EVIDENCE] README.md:114-116; configs/run_multistep.yaml:11-18; configs/eval_multistep.yaml:1-4; outputs/20260202_141735_63db48/candidate_count_summary.json

6) calculator 的适用边界是什么？
- 回答：计算器用于从检索证据中抽取数值并执行算术计算，属于数值 QA 场景，需以 numeric_metrics.json 与 numeric_per_query.jsonl 的评测口径界定有效性。[EVIDENCE] README.md:124-138; scripts/eval_numeric.py:216-234

7) 若多步检索或计算器未带来提升怎么办？
- 回答：绪论不预设性能结论，结果部分将以 outputs/<run_id> 的真实指标为准，必要时讨论局限性。[EVIDENCE] thesis/figures/FIGURE_CATALOG.md:3-45

8) 论文中如何标注 run_id 与证据来源？
- 回答：统一使用 outputs/<run_id>/... 进行引用，并在方法与实验设置中说明 run_id 的复现性与产物结构。[EVIDENCE] README.md:26-29; 仓库地图.pdf:page 1

9) 是否有数据泄露或划分不一致风险？
- 回答：数据划分由 prepare_data.yaml 驱动并落盘为 train/dev/test；具体划分与比例将在实验设置中明确说明。[EVIDENCE] configs/prepare_data.yaml:1-7

10) 与已有金融 RAG 工作的关系如何界定？
- 回答：相关工作将在后续章节补充文献对照，目前仅基于任务定义与数据集背景完成绪论定位。[EVIDENCE] TODO
