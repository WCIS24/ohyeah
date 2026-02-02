# 方法—实现对照表

Purpose:
- 将方法章的模块描述与仓库实现一一对齐，便于审查与复现。

How to use:
- 写作或审稿时按模块查找对应脚本/配置/产物。

| Module/Concept | What to describe in thesis | Repo implementation (path + symbol) | Key configs controlling it | Output artifacts (files) | Notes/TODO |
| --- | --- | --- | --- | --- | --- |
| 数据准备 | 字段映射、切分比例、随机种子与统计输出 | scripts/prepare_data.py:main | configs/prepare_data.yaml | data/processed/*.jsonl; outputs/<run_id>/data_stats.json; outputs/<run_id>/config.yaml | 若需数据规模，请引用 outputs/<run_id>/data_stats.json |
| 语料分块 | 证据文本分块、chunk_id 生成方式 | scripts/build_corpus.py:main | configs/build_corpus.yaml | data/corpus/chunks.jsonl | chunk_id 规则位于 build_corpus.py:84-96 |
| HybridRetriever | BM25 + dense 融合、bm25/dense/hybrid 模式 | src/retrieval/retriever.py:HybridRetriever | configs/run_baseline.yaml (mode/alpha/top_k) | 内存索引（FAISS 或 brute-force） | 需说明 FAISS 不可用时的回退策略 |
| Baseline 预测 | 单步检索 + 模板式答案生成 | scripts/run_baseline.py:main | configs/run_baseline.yaml | outputs/<run_id>/predictions.jsonl | placeholder_generate 仅为基线占位生成 |
| 检索评测 | Recall@K/MRR@K 计算与写入 | src/retrieval/eval_utils.py:compute_retrieval_metrics; scripts/eval_retrieval.py:main | configs/eval_retrieval.yaml | outputs/<run_id>/metrics.json; per_query_results.jsonl | 评测口径需与 k_values 对齐 |
| 多步检索 | 规划/缺口检测/停止条件/合并策略 | src/multistep/engine.py:MultiStepRetriever | configs/run_multistep.yaml | outputs/<run_id>/multistep_traces.jsonl; retrieval_results.jsonl | 需说明 top_k_each_step 与 top_k_final 的作用 |
| 多步检索评测 | 评测 + baseline 对比 delta | scripts/eval_multistep_retrieval.py:main | configs/eval_multistep.yaml | outputs/<run_id>/metrics.json; delta_vs_baseline.json | baseline_metrics_path 必须指向有效 run_id |
| 计算器流程 | 事实抽取 + 计算 + gate 回退 | scripts/run_with_calculator.py:main | configs/run_with_calculator.yaml | outputs/<run_id>/facts.jsonl; results_R.jsonl; calc_traces.jsonl; predictions_calc.jsonl | gate 规则在 run_with_calculator.py:244-269 |
| 数值评测 | numeric_em 与误差统计 | scripts/eval_numeric.py:main | configs/eval_numeric.yaml | outputs/<run_id>/numeric_metrics.json; numeric_per_query.jsonl | precision 参数决定数值对齐 |
| 产物规范 | run_id 生成与 logs/config 落盘 | src/finder_rag/utils.py:generate_run_id | README.md:26-29 | outputs/<run_id>/logs.txt; config.yaml | run_id 由 UTC 时间戳+UUID 组成 |
