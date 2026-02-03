# 第四章 实验与结果

4.1 实验设置
本章实验基于 FinDER 数据集，采用 train/dev/test 划分（4562/570/571），并在 dev 上构建复杂子集（243 条）与数值子集；这些统计已汇总到 docs/data_stats.json。[EVIDENCE] docs/data_stats.json

检索评测使用 Recall@K 与 MRR@K，K 取 [1,5,10]；数值评测使用 numeric_em、rel_error_mean、coverage 等指标，口径由 eval_numeric 实现。[EVIDENCE] configs/step6_base.yaml:64-71; src/retrieval/eval_utils.py:38-107; scripts/eval_numeric.py:151-234

Step6 主结果使用统一的 run_experiment 入口，覆盖 baseline / multistep / calculator 组合；post_ft 相关实验使用 retriever_ft 产物 models/retriever_ft/latest。[EVIDENCE] thesis_text/phase_fix/outputs_index.md; scripts/run_experiment.py:76-259; scripts/train_retriever.py:316-324

4.2 主结果对比
在 Full dev 上，pre_ft_baseline 的 Recall@10 为 0.3246，MRR@10 为 0.2030；post_ft_baseline 的 Recall@10 为 0.3789，MRR@10 为 0.2554。[EVIDENCE] thesis_text/phase5/main_results.csv; outputs/20260130_014940_21aa62_m01/summary.json; outputs/20260130_014940_21aa62_m02/summary.json

在 Complex 子集上，pre_ft_baseline 的 Recall@10 为 0.3457，MRR@10 为 0.2330；post_ft_baseline 的 Recall@10 为 0.3951，MRR@10 为 0.2961。[EVIDENCE] thesis_text/phase5/main_results.csv; outputs/20260130_014940_21aa62_m01/summary.json; outputs/20260130_014940_21aa62_m02/summary.json

calculator 开启后，检索指标与 baseline 相同（retrieval_full/complex 来自同一检索流程），但 numeric 指标可从 numeric_dev 获得：numeric_em=0.3964，rel_error_mean=689.2285，coverage=0.6180。[EVIDENCE] thesis_text/phase5/main_results.csv; outputs/20260130_014940_21aa62_m04/summary.json

4.3 组件贡献（baseline → multistep → calculator）
在 post_ft 设置下，multistep 使 Full/Complex 的 MRR@10 有轻微变化（例如 full_mrr10 由 0.2554 变为 0.2556），而 Recall@10 保持不变；该差异来自 multistep 的 merge 与 stop 策略对排序的影响。[EVIDENCE] thesis_text/phase5/main_results.csv; outputs/20260130_014940_21aa62_m02/summary.json; outputs/20260130_014940_21aa62_m03/summary.json

相对 pre_ft_baseline 的 Δ 统计显示，post_ft 系列在 Full/Complex 的 Recall@10 与 MRR@10 上均为正增量；数值指标未计算 Δ（baseline 无 numeric 指标）。[EVIDENCE] thesis_text/phase5/delta_vs_baseline.json; thesis_text/phase5/delta_vs_baseline.md

4.4 诊断分析
Step6 使用 k_list=[1,5,10]，且 multistep 的 top_k_each_step=10、top_k_final 默认为 10，因此 Recall@10 不存在候选截断风险。[EVIDENCE] configs/step6_base.yaml:31-37; configs/step6_base.yaml:64-66

numeric 指标仅在 calculator 开启时产生，说明数值推理贡献主要来自 calculator pipeline；没有 calculator 的 run 其 numeric_dev 为空。[EVIDENCE] thesis_text/phase5/main_results.csv; outputs/20260130_014940_21aa62_m04/summary.json

4.5 案例研究
成功案例（numeric）：在 run_id=20260130_014940_21aa62_m04 的 numeric_dev 中，qid=8c8c8c34 的 gold_num 与 pred_num 均为 202.0，numeric_em=1。[EVIDENCE] outputs/20260130_014940_21aa62_m04_numeric/numeric_per_query.jsonl

失败案例（numeric）：同一 run 中 qid=8b69ba09 的 pred_num 为空，numeric_em=0，表明抽取或计算失败导致数值评测未通过。[EVIDENCE] outputs/20260130_014940_21aa62_m04_numeric/numeric_per_query.jsonl

4.6 小结与局限
本章结果基于单次 run 与固定随机种子，未报告方差或显著性检验；baseline 生成不依赖外部 LLM，避免了外部 API 变动带来的不确定性，但也限制了生成端的上限。[EVIDENCE] configs/step6_base.yaml:74-77; docs/repro_env_and_llm_dependency.md
