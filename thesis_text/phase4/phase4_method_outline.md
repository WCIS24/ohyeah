# 第三章 方法（Method）提纲 v1

Purpose:
- 固化方法章的写作顺序与证据路径，确保与仓库实现一一对应。

How to use:
- 写作时按 3.1–3.7 展开，每个小节只使用下方证据路径，不补写实验结果。

## 3.1 任务形式化与符号约定
- 要写什么：统一数据记录字段（qid/query/answer/evidences）、检索输出与答案输出的接口约定。
- Evidence paths:
  - configs/prepare_data.yaml:11-20
  - scripts/prepare_data.py:126-133
  - scripts/run_baseline.py:128-142
  - scripts/run_multistep_retrieval.py:166-213
  - scripts/run_with_calculator.py:147-152

## 3.2 数据与索引构建
- 要写什么：数据切分、字段映射、统计写入；证据文本分块与语料索引构建。
- Evidence paths:
  - configs/prepare_data.yaml:1-20
  - scripts/prepare_data.py:64-145
  - configs/build_corpus.yaml:1-6
  - scripts/build_corpus.py:67-105

## 3.3 单步检索 baseline
- 要写什么：HybridRetriever 组成（BM25 + dense）、模式切换（bm25/dense/hybrid）、top_k 与 alpha 控制；baseline 预测格式。
- Evidence paths:
  - configs/run_baseline.yaml:4-12
  - scripts/run_baseline.py:86-142
  - src/retrieval/retriever.py:83-157

## 3.4 多步检索（multistep）
- 要写什么：多步配置（max_steps/top_k_each_step/top_k_final/novelty/stop）、Planner/Gap/Refiner/Stop 组件与合并策略；输出文件与字段。
- Evidence paths:
  - configs/run_multistep.yaml:1-21
  - scripts/run_multistep_retrieval.py:127-213
  - src/multistep/engine.py:12-197
  - README.md:109-116

## 3.5 证据整合与答案生成
- 要写什么：baseline 使用模板式答案生成；calculator 流程内的 fallback 与 used_chunks 记录。
- Evidence paths:
  - scripts/run_baseline.py:50-51; 128-142
  - scripts/run_with_calculator.py:235-279

## 3.6 数值计算器模块
- 要写什么：run_with_calculator 的输入、输出文件与计算流程；numeric eval 的 precision 与指标输出。
- Evidence paths:
  - configs/run_with_calculator.yaml:1-17
  - scripts/run_with_calculator.py:147-152; 184-295
  - configs/eval_numeric.yaml:1-6
  - scripts/eval_numeric.py:151-234
  - README.md:133-138

## 3.7 评测与日志/产物规范
- 要写什么：检索/QA/numeric 评测指标口径与 metrics.json 写入；run_id 生成与 outputs/<run_id>/ 结构；日志/配置落盘。
- Evidence paths:
  - scripts/eval_retrieval.py:145-166
  - src/retrieval/eval_utils.py:38-107
  - scripts/eval_qa.py:120-129
  - src/finder_rag/metrics.py:13-23
  - scripts/eval_numeric.py:154-234
  - src/finder_rag/utils.py:11-17
  - README.md:26-29
  - scripts/prepare_data.py:64-81; 140-145
