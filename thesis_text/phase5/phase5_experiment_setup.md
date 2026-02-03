# Phase 5 实验设置

Purpose:
- 固化实验设置（数据、切分、指标、环境、复现入口）并提供证据路径。

How to use:
- 直接引用到实验章 4.1，所有事实均带 [EVIDENCE]。

## 数据与切分
- FinDER 数据总量与 train/dev/test 划分：总量 5703，train=4562，dev=570，test=571。[EVIDENCE] docs/data_stats.json
- dev 复杂子集规模与比例：complex_size=243，占比约 0.4263。[EVIDENCE] docs/data_stats.json

## 子集定义与路径
- 复杂子集路径：data/subsets/dev_complex_qids.txt。[EVIDENCE] docs/data_stats.json; configs/step6_base.yaml:66-68
- 数值子集路径：data/subsets/dev_numeric_qids.txt。[EVIDENCE] configs/step6_base.yaml:66-69

## 评测指标与口径
- 检索指标：Recall@K / MRR@K，K 取值来自 eval.k_list（[1,5,10]）。[EVIDENCE] configs/step6_base.yaml:64-66; src/retrieval/eval_utils.py:38-107
- QA 指标：Exact Match (EM) 与 token_f1，定义在 eval_qa 实现。[EVIDENCE] scripts/eval_qa.py:120-129; src/finder_rag/metrics.py:13-23
- 数值指标：numeric_em / rel_error_mean / coverage 等，来自 eval_numeric 输出。[EVIDENCE] scripts/eval_numeric.py:151-234

## 模型与环境
- baseline 生成不依赖外部 LLM，采用模板式生成；因此实验可在本地复现。[EVIDENCE] docs/repro_env_and_llm_dependency.md; scripts/run_baseline.py:50-51
- post_ft 相关实验使用 retriever fine-tune 产物 models/retriever_ft/latest。[EVIDENCE] thesis_text/phase_fix/outputs_index.md; scripts/train_retriever.py:316-324

## 复现入口（主结果 Step6）
- 见 outputs_index 对应 Step6 run_id 的 run_experiment 命令与 outputs 路径。[EVIDENCE] thesis_text/phase_fix/outputs_index.md
