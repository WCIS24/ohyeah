# 第二章 相关工作 — 三级标题提纲

## 2.1 金融问答与检索增强范式
### 本节要回答的审稿人问题
- 金融领域问答为何需要检索增强与证据可追溯性？
### 需要补的外部文献类型
- 金融 QA 与金融事实核验方向代表性工作（近三年）
- RAG 基础范式与检索增强生成综述类工作
### 与本项目相关的仓库证据路径
- 金融AI选题评价.pdf:page 1
- README.md:41-131

## 2.2 多跳/多步检索与查询改写
### 本节要回答的审稿人问题
- 多步检索的动机与常见策略是什么？
### 需要补的外部文献类型
- Multi-hop Retrieval / Multi-step Retrieval / Query Reformulation 代表性方法（近三年）
### 与本项目相关的仓库证据路径
- 金融AI选题评价.pdf:page 1
- configs/run_multistep.yaml:1-21
- scripts/run_multistep_retrieval.py

## 2.3 工具增强与数值推理
### 本节要回答的审稿人问题
- 为何需要工具或计算器来处理数值问题？
### 需要补的外部文献类型
- Tool-augmented RAG / Numeric Reasoning / Calculator 模块相关研究（近三年）
### 与本项目相关的仓库证据路径
- README.md:118-138
- scripts/run_with_calculator.py
- scripts/eval_numeric.py:216-234

## 2.4 数据集与评测口径
### 本节要回答的审稿人问题
- 为什么选择 FinDER，以及常用指标口径是什么？
### 需要补的外部文献类型
- 金融 QA 数据集综述、FinDER 论文/技术报告、评测指标基准工作
### 与本项目相关的仓库证据路径
- 金融AI选题评价.pdf:page 1
- src/retrieval/eval_utils.py:38-106
- scripts/eval_qa.py:120-129
- scripts/eval_numeric.py:216-234

## 2.5 小结：本工作的定位与差异
### 本节要回答的审稿人问题
- 本工作与现有方法的主要差异与边界在哪里？
### 需要补的外部文献类型
- 与多步检索/数值推理相关的代表性对比工作
### 与本项目相关的仓库证据路径
- README.md:41-131
- 仓库地图.pdf:page 1
- thesis_text/phase1/phase1_contribution_statements.md
