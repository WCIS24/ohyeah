第三章 方法

3.1 任务形式化与符号约定
本研究将原始数据统一为包含 qid、query、answer、evidences 的记录结构，通过 prepare_data 的 field_map 将原始列映射到统一字段，并将 evidences 解析为带 evidence_id 的结构化列表，保证检索与问答模块共享一致的输入格式。[EVIDENCE] configs/prepare_data.yaml:11-20; src/data/finder.py:65-123; scripts/prepare_data.py:114-133

在本文的接口约定中，检索模块产出“证据集合”，而答案模块产出最终答案：baseline 的 predictions.jsonl 记录 qid、pred_answer 与 used_chunks，多步检索的 retrieval_results.jsonl 记录 final_top_chunks 与 all_collected_chunks，计算器流程额外生成 predictions_calc.jsonl 等文件并保留检索结果以便回溯。[EVIDENCE] scripts/run_baseline.py:128-142; scripts/run_multistep_retrieval.py:166-213; scripts/run_with_calculator.py:147-152

3.2 数据与索引构建
数据准备阶段由 prepare_data 负责：读取 dataset/finder_dataset.csv（FinDER CSV），按 train/dev/test 比例切分并写入 data/processed/*.jsonl，同时在 outputs/<run_id>/ 下落盘 data_stats.json 与 config.yaml，并记录随机种子以保证可复现性。[EVIDENCE] configs/prepare_data.yaml:1-20; scripts/prepare_data.py:64-145

数据集总量与拆分规模已汇总为 docs/data_stats.json（含 train/dev/test 计数与 dev 复杂子集比例），可作为方法章中的数据规模证据。[EVIDENCE] docs/data_stats.json; outputs/20260202_165254_c4b131/data_stats.json; outputs/20260202_165303_b04a7b/subsets_stats.json

语料与索引构建由 build_corpus 完成：从 data/processed 的 evidences 字段抽取证据文本，按 chunk_size=1000 与 overlap=100 进行分块，并写入 data/corpus/chunks.jsonl，chunk 的 meta 中包含 source_qid、evidence_id 与 chunk_id 等信息。[EVIDENCE] configs/build_corpus.yaml:1-6; scripts/build_corpus.py:67-105

整体流水线按 README 中的脚本入口顺序组织，便于从数据处理到评测的逐步复现。[EVIDENCE] README.md:41-131

```text
prepare_data(configs/prepare_data.yaml)
build_corpus(configs/build_corpus.yaml)
eval_retrieval(configs/eval_retrieval.yaml)
run_baseline(configs/run_baseline.yaml) -> outputs/<run_id>/predictions.jsonl
eval_qa(configs/eval_qa.yaml, predictions.jsonl, data/processed/dev.jsonl)
run_multistep_retrieval(configs/run_multistep.yaml) -> outputs/<run_id>/retrieval_results.jsonl
eval_multistep_retrieval(configs/eval_multistep.yaml, retrieval_results.jsonl)
run_with_calculator(configs/run_with_calculator.yaml, optional multistep results)
eval_numeric(configs/eval_numeric.yaml, predictions_calc.jsonl)
```

3.3 单步检索 baseline
单步检索使用 HybridRetriever：同时维护 BM25 与 dense 向量索引，支持 bm25/dense/hybrid 三种模式，并用 alpha 融合归一化得分；当 use_faiss 启用但系统无 FAISS 时回退到 brute-force 计算。该 baseline 属于检索增强（RAG）流程，检索器与生成模块按接口分离。[EVIDENCE] README.md:1-3; src/retrieval/retriever.py:83-145; src/retrieval/retriever.py:101-109

baseline 运行时读取 dev 分片与 corpus，按 top_k 与 alpha 检索证据，输出 predictions.jsonl（qid、pred_answer、used_chunks）；pred_answer 采用模板式生成函数 placeholder_generate，从检索片段中截取文本构造答案。[EVIDENCE] configs/run_baseline.yaml:4-12; scripts/run_baseline.py:86-142; scripts/run_baseline.py:50-51

baseline 的生成不依赖外部 LLM API，当前实现为模板式生成；最小复现分支（retrieval-only / full QA）已整理于 docs/repro_env_and_llm_dependency.md。[EVIDENCE] scripts/run_baseline.py:50-51; docs/repro_env_and_llm_dependency.md

3.4 多步检索（multistep）
多步检索由 MultiStepRetriever 执行，配置项包含 max_steps、top_k_each_step、top_k_final、novelty_threshold 与 stop_no_new_steps，并支持 gate/refiner 等开关；这些配置来自 run_multistep.yaml 并在运行时写入 MultiStepConfig。[EVIDENCE] configs/run_multistep.yaml:1-21; scripts/run_multistep_retrieval.py:127-148; src/multistep/engine.py:12-27

多步检索内部使用 StepPlanner 规划检索步骤，通过 gap 检测与 stop criteria 决定是否继续，并在必要时调用 refiner 生成下一步查询；最终通过 merge_strategy 聚合候选并在不足时回退补齐至 final_top_k。[EVIDENCE] src/multistep/engine.py:33-191

StepPlanner 的 query_type 规则、gap 检测逻辑、停止条件（EMPTY_RESULTS / NO_GAP / MAX_STEPS / NO_NEW_EVIDENCE）与 query refiner 的改写规则已在 docs/multistep_design.md 中做可复述化整理。[EVIDENCE] docs/multistep_design.md; src/multistep/planner.py:7-41; src/multistep/gap.py:51-84; src/multistep/stop.py:26-53; src/multistep/refiner.py:19-34

多步检索输出 multistep_traces.jsonl 与 retrieval_results.jsonl，分别记录逐步检索轨迹与每个 query 的最终候选（final_top_chunks / all_collected_chunks、stop_reason、steps_used）。[EVIDENCE] scripts/run_multistep_retrieval.py:166-213; README.md:109-112

3.5 证据整合与答案生成
baseline 的答案生成采用模板式占位策略：从检索到的证据片段中截取内容构造 pred_answer，并记录 used_chunks 以保持“答案—证据”可追溯关系。[EVIDENCE] scripts/run_baseline.py:50-51; scripts/run_baseline.py:128-141

在 calculator 流程中，若计算结果通过 gate 规则则基于计算结果生成 pred_answer；否则回退到检索片段与 placeholder_generate，并记录 fallback_reason 与 used_chunks，以保证失败路径同样可回溯。[EVIDENCE] scripts/run_with_calculator.py:235-291

3.6 数值计算器模块
run_with_calculator 支持两种输入：直接调用检索器或复用 multistep 的 retrieval_results；输出 retrieval_results.jsonl、facts.jsonl、results_R.jsonl、calc_traces.jsonl 与 predictions_calc.jsonl，为后续 numeric 评测提供输入与可解释轨迹。[EVIDENCE] configs/run_with_calculator.yaml:1-17; scripts/run_with_calculator.py:147-152; scripts/run_with_calculator.py:184-211; README.md:133-138

计算器模块的任务类型（yoy/diff/share/multiple）、事实抽取规则与 gate 回退条件已整理于 docs/calculator_design.md，对应代码在 src/calculator 与 run_with_calculator.py 中可追溯。[EVIDENCE] docs/calculator_design.md; src/calculator/compute.py:9-59; src/calculator/extract.py:7-154; scripts/run_with_calculator.py:244-279

数值评测由 eval_numeric 执行，按 precision 参数计算 numeric_em 与误差统计，逐条写入 numeric_per_query.jsonl，并汇总到 numeric_metrics.json 以供实验表格引用。[EVIDENCE] configs/eval_numeric.yaml:1-6; scripts/eval_numeric.py:151-234

3.7 评测与日志/产物规范
检索评测通过 compute_retrieval_metrics 计算 Recall@K / MRR@K 等指标，eval_retrieval 写出 metrics.json 与 per_query_results.jsonl，为检索阶段提供统一评测口径。[EVIDENCE] src/retrieval/eval_utils.py:38-107; scripts/eval_retrieval.py:145-166

问答评测使用 Exact Match (EM) 与 token_f1 作为核心指标，数值评测使用 numeric_em 与误差统计字段，并统一写入各自的 metrics.json / numeric_metrics.json 文件。[EVIDENCE] src/finder_rag/metrics.py:13-23; scripts/eval_qa.py:120-129; scripts/eval_numeric.py:216-234

所有脚本使用 run_id 生成 outputs/<run_id>/ 目录并落盘 config.yaml、logs.txt 等文件；run_id 由 UTC 时间戳与短 UUID 组成，同时记录 git_commit 以支持复现。[EVIDENCE] src/finder_rag/utils.py:11-17; README.md:26-29; scripts/prepare_data.py:64-81; scripts/prepare_data.py:140-145
